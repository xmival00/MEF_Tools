from shutil import rmtree
from unittest import TestCase
from mef_tools.io import MefWriter, create_pink_noise, check_data_integrity
import os
import numpy as np
basedir = os.path.abspath(os.path.dirname(__file__))


class TestMefWriter(TestCase):
    def setUp(self):
        session_name = 'test_session'
        self.session_path = f'{basedir}/{session_name}.mefd'
        self.pass1 = 'pass1'
        self.pass2 = 'pass2'
        self.mef_writer = MefWriter(session_path=self.session_path, overwrite=True, password1=self.pass1, password2=self.pass2)

    def tearDown(self):
        del self.mef_writer
        rmtree(self.session_path)

    def test_write_data(self):
        # multiple write test called
        # define how much is written
        secs_to_write = 30
        secs_to_seg2 = 5

        # define start of data uutc in uUTC time
        start_time = 1578715810000000
        # define end of data in uUTC time
        end_time = int(start_time + 1e6 * secs_to_write)

        writer = self.mef_writer
        writer.max_nans_written = 100

        # create test data
        fs = 500
        low_b = -10
        up_b = 10
        precision = 3
        test_data_1 = create_pink_noise(fs, secs_to_write, low_b, up_b)
        channel = 'test_channel_1'
        test_data_1[1200:6232] = np.nan
        test_data_1[8542:8599] = np.nan
        writer.write_data(test_data_1, channel, start_time, fs, precision=precision)
        # check stored data and check nans
        read_data = writer.session.read_ts_channels_uutc(channel, [start_time, end_time])
        read_data_nans = np.isnan(read_data)
        write_data_nans = np.isnan(test_data_1)

        self.assertTrue(np.array_equal(read_data_nans, write_data_nans))
        self.assertTrue(check_data_integrity(test_data_1, read_data, precision ))
        # append new data
        secs_to_append = 5
        discont_length = 1

        append_time = end_time + int(discont_length * 1e6)
        append_end = int(append_time + 1e6 * secs_to_append)
        test_data_2 = create_pink_noise(fs, secs_to_append, low_b, up_b)
        writer.write_data(test_data_2, channel, append_time, fs)

        # check stored data and check nans
        read_data = writer.session.read_ts_channels_uutc(channel, [append_time, append_end])
        read_data_nans = np.isnan(read_data)
        write_data_nans = np.isnan(test_data_2)
        self.assertTrue(np.array_equal(read_data_nans, write_data_nans))
        self.assertTrue(check_data_integrity(test_data_2, read_data, precision))

        # new segment
        gap_time = 3.36 * 1e6
        newseg_time = append_end + int(gap_time)
        newseg_end = int(newseg_time + 1e6 * secs_to_seg2)
        test_data_3 = create_pink_noise(fs, secs_to_seg2, low_b, up_b)
        test_data_3[30:540] = np.nan
        test_data_3[660:780] = np.nan
        writer.write_data(test_data_3, channel, newseg_time, fs, new_segment=True, )

        # check stored data and check nans
        read_data = writer.session.read_ts_channels_uutc(channel, [newseg_time, newseg_end])
        read_data_nans = np.isnan(read_data)
        write_data_nans = np.isnan(test_data_3)
        self.assertTrue(np.array_equal(read_data_nans, write_data_nans))
        self.assertTrue(check_data_integrity(test_data_3, read_data, precision))

        # append to seg 2 with different session
        append_time = newseg_end + int(discont_length * 1e6)
        append_end = int(append_time + 1e6 * secs_to_append)
        test_data_4 = create_pink_noise(fs, secs_to_append, low_b, up_b)
        test_data_4[20:630] = np.nan
        test_data_4[660:780] = np.nan

        writer2 = MefWriter(session_path=self.session_path, overwrite=False, password1=self.pass1, password2=self.pass2)
        writer2.write_data(test_data_4, channel, append_time, fs, )

        # check stored data and check nans
        writer._reload_session_info()
        read_data = writer.session.read_ts_channels_uutc(channel, [append_time, append_end])
        read_data_nans = np.isnan(read_data)
        write_data_nans = np.isnan(test_data_4)
        self.assertTrue(np.array_equal(read_data_nans, write_data_nans))
        self.assertTrue(check_data_integrity(test_data_4, read_data, precision))

        # test all data channel 1
        write_data_all = np.concatenate((test_data_1, test_data_2, test_data_3, test_data_4))

        write_data_nans = np.isnan(write_data_all)
        read_data_all = writer.session.read_ts_channels_sample(channel, [None, None]) * writer.channel_info[channel]['ufact'][0]
        read_data_nans = np.isnan(read_data_all)
        self.assertTrue(np.allclose(write_data_all[~write_data_nans], read_data_all[~read_data_nans], atol=0.1**(precision-1)))
        # write new channel data
        secs_to_write = 30

        # define start of data uutc in uUTC time
        start_time = 1578716810000000
        # define end of data in uUTC time
        end_time = int(start_time + 1e6 * secs_to_write)

        writer = self.mef_writer
        writer.max_nans_written = 100

        # create test data with low fs
        fs = 31
        low_b = -1
        up_b = 1
        precision = 3
        test_data_5 = create_pink_noise(fs, secs_to_write, low_b, up_b)
        channel = 'test_channel_2'
        test_data_5[120:623] = np.nan
        # store data with inferred precision
        writer.write_data(test_data_5, channel, start_time, fs)

        # assert channel 2
        # check stored data and check nans
        read_data = writer.session.read_ts_channels_uutc(channel, [start_time, end_time]) * writer.channel_info[channel]['ufact'][0]
        read_data_nans = np.isnan(read_data)
        write_data_nans = np.isnan(test_data_5)
        self.assertTrue(np.array_equal(read_data_nans, write_data_nans))
        self.assertTrue(np.allclose(test_data_5[~write_data_nans], read_data[~read_data_nans], atol=0.1 ** (precision - 1)))