"""
Module with auxillary
    jit-compiled functions
    for resize of
    DICOM-scans
"""

from numba import jit
import scipy.ndimage
import numpy as np


@jit(nogil=True)
def resize_patient_numba(patient, out_patient, res, shape=None, order=3,
                         res_factor=None, padding='edge', spacing=None):
    """ Resize 3d-scan for one patient and put it into out_patient array.
            If res_factor is supplied, use this arg for interpolation.
            O/w infer resize factor from out_patient.shape.

    Args
        patient: ndarray with patient data
        out_patient: ndarray, in which patient data
            after resize should be put
        order: order of interpolation
        res: out array for the whole batch
            not needed here, will be used later by post default
        res_factor: resize factor that has to used for the interpolation
            when not None, can yield array of shape != out_patient.shape.
            In this case crop/pad is used
        padding: mode of padding, can be any of the modes used by np.pad
        spacing: not needed here, included because of technical reasons
    Return:
        tuple (res, out_patient.shape)

    * shape of resized array has to be inferred
        from out_patient
    """
    # an actual shape is inferred from out_patient
    _ = shape
    shape = out_patient.shape

    # define resize factor, perform resizing and put the result into out_patient
    if res_factor is None:
        res_factor = np.array(out_patient.shape) / np.array(patient.shape)
        out_patient[:, :, :] = scipy.ndimage.interpolation.zoom(patient, res_factor,
                                                                order=order)
    else:
        out_patient[:, :, :] = to_shape((scipy.ndimage.interpolation.
                                         zoom(patient, res_factor, order=order)),
                                        shape=shape, padding=padding)


    # return out-array for the whole batch
    # and shape of out_patient
    return res, out_patient.shape


def to_shape(data, shape, padding):
    """ Crop\pad 3d-array of arbitrary shape s.t. it be a 3d-array
        of shape=shape

    Args:
        data: 3d-array for reshaping
        shape: needed shape, tuple/list/ndaray of len = 3
        padding: mode of padding, can be any of the modes used by np.pad
    Return:
        cropped and padded data
    """
    # calculate shapes discrepancy
    data_shape = np.asarray(data.shape)
    shape = np.asarray(shape)
    overshoot = data_shape - shape

    # calclate crop params and perform crop
    zeros = np.zeros_like(overshoot)
    crop_dims = np.maximum(overshoot, 0)
    crop_first = crop_dims // 2
    crop_trailing = crop_dims - crop_first
    slices = [slice(first, dim_shape - trailing)
              for first, trailing, dim_shape in zip(crop_first, crop_trailing, data_shape)]
    data = data[slices]

    # calculate padding params and perform padding
    pad_dims = -np.minimum(overshoot, 0)
    pad_first = pad_dims // 2
    pad_trailing = pad_dims - pad_first
    pad_params = [(first, trailing) 
                  for first, trailing in zip(pad_first, pad_trailing)]
    data = np.pad(data, pad_width=pad_params, mode=padding)

    # return cropped/padded array
    return data


