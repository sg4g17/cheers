'''
    Created by Tao
    Edited by Ding

    Reference:
        http://haythamfayek.com/2016/04/21/speech-processing-for-machine-learning.html

    Notes:
        frames_ham and frames_kai is the final value after three steps,type is <class 'np.ndarray'>
'''

import numpy as np
from scipy.fftpack import dct


def pre_emphasis(signal, coef=0.97):
    '''
    # step 1:pre_emphasis
    :param signal:
    :param coef:
    :return:
        An array
    '''
    return np.append(signal[0], signal[1:] - coef * signal[:-1])


def framing(signal, sample_rate, frame_size=0.025, frame_stride=0.01):
    '''
    # Step 2:Framing
    :param signal:
    :param frame_size:      frame_size=0.025 # 25 ms for the frame size
    :param frame_stride:    frame_stride =0.01 # a 10 ms stride (15 ms overlap)
    :return:

    '''
    # Convert from seconds to samples
    frame_length = frame_size * sample_rate
    frame_step = frame_stride * sample_rate
    frame_length = int(round(frame_length))
    frame_step = int(round(frame_step))

    signal_length = len(signal)

    # Make sure that we have at least 1 frame
    num_frames = int(np.ceil(float(np.abs(signal_length - frame_length)) / frame_step))

    pad_signal_length = num_frames * frame_step + frame_length
    z = np.zeros((pad_signal_length - signal_length))

    # Pad Signal to make sure that all frames have equal number of samples without truncating any samples from the original signal
    pad_signal = np.append(signal, z)

    indices = np.tile(np.arange(0, frame_length), (num_frames, 1)) + np.tile(np.arange(0, num_frames * frame_step, frame_step), (frame_length, 1)).T

    return pad_signal[indices.astype(np.int32, copy=False)], frame_length


def window(frames, frame_length, method='hamming'):
    '''
    # Step3 window function
    :param frames:
    :param frame_length:
    :param method:
    :return:
    '''
    # kaiser window
    if method == 'kaiser':
        return np.kaiser(frame_length, 5) * frames

    # hamming window
    elif method == 'hamming':
        return np.hamming(frame_length) * frames


def fft_filterbank(frames_ham, sample_rate, n=512, nfilt=40, normalize=False):
    '''
    # step4 FFT and power spectrum
    # step5 filter banks
    :param frames_ham: 
    :param n: the n of n-point FFT
    :param nfilt: the n of n-point FFT
    :return: 
    '''
    # Magnitude of the FFT
    mag_frames = np.absolute(np.fft.rfft(frames_ham, n))  
    # Power Spectrum
    pow_frames = ((1.0 / n) * ((mag_frames) ** 2))

    low_freq_mel = 0
    high_freq_mel = (2595 * np.log10(1 + (sample_rate / 2) / 700))  # Convert Hz to Mel
    mel_points = np.linspace(low_freq_mel, high_freq_mel, nfilt + 2)  # Equally spaced in Mel scale
    hz_points = (700 * (10 ** (mel_points / 2595) - 1))  # Convert Mel to Hz
    bin = np.floor((n + 1) * hz_points / sample_rate)

    fbank = np.zeros((nfilt, int(np.floor(n / 2 + 1))))
    for m in range(1, nfilt + 1):
        f_m_minus = int(bin[m - 1])  # left
        f_m = int(bin[m])  # center
        f_m_plus = int(bin[m + 1])  # right

        for k in range(f_m_minus, f_m):
            fbank[m - 1, k] = (k - bin[m - 1]) / (bin[m] - bin[m - 1])
        for k in range(f_m, f_m_plus):
            fbank[m - 1, k] = (bin[m + 1] - k) / (bin[m + 1] - bin[m])
    filter_banks = np.dot(pow_frames, fbank.T)

    # Numerical Stability
    filter_banks = np.where(filter_banks == 0, np.finfo(float).eps, filter_banks)

    # dB I don't understand the 20 here...
    if normalize:
        filter_banks -= (np.mean(filter_banks, axis=0) + 1e-8)

    return 20 * np.log10(filter_banks)
    

def mfccs(f_bank, num_ceps=12, cep_lifter=22, normalize=False):
    '''

    :param f_bank:
    :param num_ceps:
    :param cep_lifter:
    :param normalize:
    :return:
    '''
    mfcc = dct(f_bank, type=2, axis=1, norm='ortho')[:, 1: (num_ceps + 1)]  # Keep 2-13

    (nframes, ncoeff) = mfcc.shape
    n = np.arange(ncoeff)
    lift = 1 + (cep_lifter / 2) * np.sin(np.pi * n / cep_lifter)
    if normalize:
        mfcc *= lift
    else:
        mfcc -= (np.mean(mfcc, axis=0) + 1e-8)

    return mfcc






