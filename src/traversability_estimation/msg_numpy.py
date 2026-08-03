"""Conversions between ROS 2 messages and NumPy arrays.

Drop-in replacement for the ``msgify`` / ``numpify`` helpers of ``ros_numpy``
(ROS 1) and ``ros2_numpy``, implemented on top of plain NumPy and the
``sensor_msgs_py`` module shipped with ROS 2, so that no extra package has to
be installed.

Supported message types: ``sensor_msgs/PointCloud2`` and ``sensor_msgs/Image``.
"""
from __future__ import absolute_import, division, print_function

import sys

import numpy as np
from numpy.lib.recfunctions import unstructured_to_structured
from sensor_msgs.msg import Image, PointCloud2, PointField
from sensor_msgs_py.point_cloud2 import dtype_from_fields

__all__ = ['msgify', 'numpify', 'cloud_to_numpy', 'numpy_to_cloud',
           'image_to_numpy', 'numpy_to_image', 'fields_from_dtype']

_DATATYPES = {
    np.dtype(np.int8): PointField.INT8,
    np.dtype(np.uint8): PointField.UINT8,
    np.dtype(np.int16): PointField.INT16,
    np.dtype(np.uint16): PointField.UINT16,
    np.dtype(np.int32): PointField.INT32,
    np.dtype(np.uint32): PointField.UINT32,
    np.dtype(np.float32): PointField.FLOAT32,
    np.dtype(np.float64): PointField.FLOAT64,
}

# Image encoding -> (numpy dtype, number of channels).
_ENCODINGS = {
    'mono8': (np.uint8, 1),
    'mono16': (np.uint16, 1),
    'bgr8': (np.uint8, 3),
    'rgb8': (np.uint8, 3),
    'bgra8': (np.uint8, 4),
    'rgba8': (np.uint8, 4),
    'bayer_rggb8': (np.uint8, 1),
    'bayer_bggr8': (np.uint8, 1),
    'bayer_gbrg8': (np.uint8, 1),
    'bayer_grbg8': (np.uint8, 1),
}

# Types of the OpenCV-style encodings, e.g. "32FC1".
_CV_TYPES = {
    '8U': np.uint8, '8S': np.int8,
    '16U': np.uint16, '16S': np.int16,
    '32S': np.int32, '32F': np.float32,
    '64F': np.float64,
}


def _encoding_to_dtype(encoding):
    """Return (numpy dtype, number of channels) for an image encoding."""
    if encoding in _ENCODINGS:
        dtype, channels = _ENCODINGS[encoding]
        return np.dtype(dtype), channels
    # OpenCV-style encoding, e.g. "32FC1" or "8UC3" ("C1" may be omitted).
    for prefix, dtype in _CV_TYPES.items():
        if encoding.startswith(prefix):
            suffix = encoding[len(prefix):]
            channels = int(suffix[1:]) if suffix.startswith('C') and suffix[1:] else 1
            return np.dtype(dtype), channels
    raise ValueError('Unsupported image encoding: %s' % encoding)


def _dtype_to_encoding(dtype, channels):
    """Return an OpenCV-style image encoding for the given dtype and channels."""
    for prefix, cv_dtype in _CV_TYPES.items():
        if np.dtype(cv_dtype) == dtype:
            return '%sC%i' % (prefix, channels)
    raise ValueError('Unsupported image dtype: %s' % dtype)


def fields_from_dtype(dtype):
    """Convert a structured NumPy dtype to a list of sensor_msgs/PointField."""
    assert dtype.names is not None, 'A structured array dtype is required.'
    fields = []
    for name in dtype.names:
        field_dtype, offset = dtype.fields[name][:2]
        if field_dtype.subdtype is not None:
            # Field with count > 1, e.g. dtype (np.float32, (3,)).
            item_dtype, shape = field_dtype.subdtype
            count = int(np.prod(shape))
        else:
            item_dtype, count = field_dtype, 1
        if item_dtype not in _DATATYPES:
            raise ValueError('Unsupported point field type: %s (%s)' % (name, item_dtype))
        fields.append(PointField(name=name, offset=offset,
                                 datatype=_DATATYPES[item_dtype], count=count))
    return fields


def cloud_to_numpy(msg, squeeze=True):
    """Convert sensor_msgs/PointCloud2 to a structured NumPy array.

    Organized clouds are returned with shape (height, width), unorganized ones
    with shape (width,), matching the ros_numpy behavior.
    """
    assert isinstance(msg, PointCloud2)
    dtype = dtype_from_fields(msg.fields, point_step=msg.point_step)
    cloud = np.frombuffer(bytearray(msg.data), dtype=dtype,
                          count=msg.height * msg.width)
    if bool(sys.byteorder != 'little') != bool(msg.is_bigendian):
        cloud = cloud.byteswap()
    cloud = cloud.reshape((msg.height, msg.width))
    if squeeze and msg.height == 1:
        cloud = cloud.reshape((msg.width,))
    return cloud


def numpy_to_cloud(cloud, stamp=None, frame_id=None):
    """Convert a (structured) NumPy array to sensor_msgs/PointCloud2."""
    if cloud.dtype.names is None:
        raise ValueError('A structured array is required, got dtype %s. '
                         'Use numpy.lib.recfunctions.unstructured_to_structured '
                         'or msgify_cloud.' % cloud.dtype)
    fields = fields_from_dtype(cloud.dtype)
    cloud = np.ascontiguousarray(cloud)
    if cloud.ndim == 1:
        cloud = cloud.reshape((1, -1))
    assert cloud.ndim == 2, 'Point cloud must be at most 2-dimensional.'
    height, width = cloud.shape

    msg = PointCloud2()
    if stamp is not None:
        msg.header.stamp = stamp
    if frame_id is not None:
        msg.header.frame_id = frame_id
    msg.height = height
    msg.width = width
    msg.fields = fields
    msg.is_bigendian = sys.byteorder != 'little'
    msg.point_step = cloud.dtype.itemsize
    msg.row_step = cloud.dtype.itemsize * width
    msg.is_dense = False
    msg.data = np.frombuffer(cloud.tobytes(), dtype=np.uint8)
    return msg


def image_to_numpy(msg):
    """Convert sensor_msgs/Image to a NumPy array."""
    assert isinstance(msg, Image)
    dtype, channels = _encoding_to_dtype(msg.encoding)
    dtype = dtype.newbyteorder('>' if msg.is_bigendian else '<')
    shape = (msg.height, msg.width, channels)
    data = np.frombuffer(bytearray(msg.data), dtype=dtype)
    data = data.reshape((msg.height, msg.step // dtype.itemsize))
    data = data[:, :msg.width * channels].reshape(shape)
    if channels == 1:
        data = data[:, :, 0]
    return data


def numpy_to_image(arr, encoding=None, stamp=None, frame_id=None):
    """Convert a NumPy array to sensor_msgs/Image."""
    arr = np.asarray(arr)
    assert arr.ndim in (2, 3), 'Image array must be 2- or 3-dimensional.'
    channels = arr.shape[2] if arr.ndim == 3 else 1
    if encoding is None:
        encoding = _dtype_to_encoding(arr.dtype, channels)
    else:
        dtype, enc_channels = _encoding_to_dtype(encoding)
        assert enc_channels == channels, \
            'Encoding %s expects %i channels, got %i.' % (encoding, enc_channels, channels)
        arr = arr.astype(dtype, copy=False)
    arr = np.ascontiguousarray(arr)

    msg = Image()
    if stamp is not None:
        msg.header.stamp = stamp
    if frame_id is not None:
        msg.header.frame_id = frame_id
    msg.height, msg.width = arr.shape[:2]
    msg.encoding = encoding
    msg.is_bigendian = int(arr.dtype.byteorder == '>'
                           or (arr.dtype.byteorder == '=' and sys.byteorder == 'big'))
    msg.step = arr.strides[0]
    msg.data = np.frombuffer(arr.tobytes(), dtype=np.uint8)
    return msg


_TO_NUMPY = {PointCloud2: cloud_to_numpy, Image: image_to_numpy}
_FROM_NUMPY = {PointCloud2: numpy_to_cloud, Image: numpy_to_image}


def numpify(msg, *args, **kwargs):
    """Convert a ROS message to a NumPy array."""
    converter = _TO_NUMPY.get(type(msg))
    if converter is None:
        raise TypeError('Cannot convert %s to a NumPy array.' % type(msg))
    return converter(msg, *args, **kwargs)


def msgify(msg_type, arr, *args, **kwargs):
    """Convert a NumPy array to a ROS message of the given type."""
    converter = _FROM_NUMPY.get(msg_type)
    if converter is None:
        raise TypeError('Cannot convert a NumPy array to %s.' % msg_type)
    return converter(arr, *args, **kwargs)


def msgify_cloud(cloud, frame, stamp, names):
    """Convert an unstructured (N, len(names)) array to sensor_msgs/PointCloud2."""
    assert cloud.ndim == 2
    cloud = unstructured_to_structured(np.asarray(cloud, dtype=np.float32), names=names)
    return numpy_to_cloud(cloud, stamp=stamp, frame_id=frame)
