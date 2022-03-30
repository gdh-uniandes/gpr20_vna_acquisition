"""Class that handles the connection to the VNA instrument.

This class provides the direct communication to the VNA device under the
VXI-11 protocol. This allows to encapsulate the communication mechanisms
for higher-level utilities.
"""

from socket import error
from vxi11 import Instrument
from vxi11.vxi11 import Vxi11Exception

# Define calibration status values
VNA_CAL_LOW = 0
VNA_CAL_MID = 1
VNA_CAL_HIGH = 2
VNA_CAL_NO_DATA = 3


class VNADriver(object):
    """Class to provide an interface to the VNA instrument of the GPR-20.

    Attributes:
        instrument (vxi11.Instrument): stores the instrument instance.
        vna_connected (bool): flag to tell if VNA is connected.
        vna_ip (str): stores the VNA IP address.
    """

    def __init__(self):
        """Initialize the VNA interface class."""
        # Define the instrument instance attribute
        self.__instrument = None

        # Define the VNA connected flag attribute
        self.__vna_connected = False

        # Define the VNA IP attribute
        self.__vna_ip = None

    def connect_to_vna(self, ip_addr):
        """Connect to the VNA with a given IP address.

        This method attempts to connect to the VNA device and to check that
        the connected device is the VNA. The connection is done using an IP
        address passed as parameter to the function (ip_addr). The device
        checks consists of comparing the received device information with the
        expected values for manufacturer and model. If VNA is connected, the
        corresponding flag will be set to 'True' and the IP address stored.

        Args:
            ip_addr (str): IP addres that the VNA will connect to.

        Returns:
            bool: 'True' if the VNA was connected properly. 'False' otherwise.
            str: message with the result of the connect procedure.
        """
        # Execute inside try/catch block
        try:
            # Create the instrument instance for VNA
            self.__instrument = Instrument(ip_addr)

            # Ask the VNA device for its identification
            response = self.__instrument.ask("*IDN?")

            # Remove the leading and trailing quotation marks
            response = response.replace('"', '')

            # Split the response on commas
            response = response.split(',')

            # Assert that manufacturer is 'Anritsu'
            assert response[0] == "Anritsu", "Device manufacturer is \
                not Anritsu"

            # Assert that device model is 'MS2026C/2'
            assert response[1] == "MS2026C/2", "Device model is not \
                MS2026C/2"

        # Return False if assertions fails
        except AssertionError as e:

            # Return 'False' to indicate an error with the message
            return False, "Different device manufacturer and/or model!"

        # Return False if VNA connection fails
        except OSError as e:

            # Return 'False' to indicate an error with the message
            return False, "VNA connection error!"

        # Set the connected flag
        self.__vna_connected = True

        # Store the used IP address
        self.__vna_ip = ip_addr

        # Return 'True' if no error is raised
        return True, "Connected to VNA device"

    def disconnect_from_vna(self):
        """Disconnect the VNA instrument.

        This method releases the connection to the VNA instrument and resets
        the flags. The instrument attribute is set to 'None'. If the VNA
        device is connected, the connection is closed before destroying the
        communication.

        Returns:
            bool: indicating that the VNA device has been disconnected.
        """
        # Checks if VNA is connected before disconnecting
        if self.__vna_connected:

            # Close connection to VNA
            self.__instrument.close()

        # Reset connection flag
        self.__vna_connected = False

        # Reset IP attribute
        self.__vna_ip = None

        # Destroy instrument attribute
        self.__instrument = None

        # Return 'True' to indicate that VNA was disconnected
        return True

    def test_connection(self):
        """Test if VNA is connected and responding.

        This mehtod tests the connection to the VNA device. The identification
        query is sent to the device. If a timeout error is raised, the method
        returns to indicate that the VNA is disconnected or unreachable.

        Returns:
            bool: 'True' if no timeout is reached. 'False' otherwise.
        """
        # Try to ask instrument identification
        try:

            # Asks the instrument its identification
            self.__instrument.ask("*IDN?")

            # Return 'True' if the response is retrieved.
            return True

        # If exception is raised, flags are reset
        except (Vxi11Exception, error) as vxi_error:

            # Return 'False' to indicate that the device cannot be reached
            return False

    def check_calibration_status(self):
        """Check VNA instrument calibration status.

        This method queries the VNA instrument to get the calibration status.
        There are two types of outcomes: a status value that can be either
        'LOW', 'MID' or 'HIGH', and no information at all. The latter type
        occurs on two circumstances. The first being that the device cannot be
        reached, and the second being that the device has no data referring
        its calibration status.

        Returns
            int: calibration status. Values are defined as constant in
                this module.
        """
        # Ask instrument's calibration status in try/except block
        try:

            # Asks instument about its calibration status
            status = int(self.__instrument.ask(
                ":SENS:CORR:COLL:STAT:ACC?"
            ))

            # Returns low calibration status
            if status == 4:
                return VNA_CAL_LOW

            # Returns mid calibration status
            elif status == 3 or status == 2:
                return VNA_CAL_MID

            # Returns high calibration status
            elif status == 1:
                return VNA_CAL_HIGH

            # Returns that no data is available
            elif status == 0:
                return VNA_CAL_NO_DATA

            # Returns no data if not in previous cases
            return VNA_CAL_NO_DATA

        # Raise exception on instrument error
        except Vxi11Exception as vxi_error:

            # Return that no data is available on calibration status
            return VNA_CAL_NO_DATA

    def set_frequency_sweep(self, f_start, f_stop, n_points):
        """Set the frequency sweep values.

        This mehtod sets the frequency sweep parameters in the VNA device.
        The frequency sweep parameters are the start and stop frequencies,
        that limit the data acquisition bandwith, and the frequency points
        that define how many samples will be acquired.

        Args:
            f_start (int): start frequency for sweep.
            f_stop (int): stop frequency for sweep.
            n_points(int): number of used frequency points.

        Returns:
            bool: 'True' if no error is raised when setting the data in the
                instrument. 'False' otherwise.
        """
        # Try to write the frequency parameters
        try:

            # Write the start frequency
            self.__instrument.write(":SENS:FREQ:STAR " + str(f_start))

            # Write the stop frequency
            self.__instrument.write(":SENS:FREQ:STOP " + str(f_stop))

            # Write the frequency points number
            self.__instrument.write(":SENS:SWE:POIN " + str(n_points))

            # Return 'True' to indicate that no error has occured
            return True

        # Hanlde if a communication error is raised
        except Vxi11Exception as vxi_error:

            # Return 'False' to indicate that an error has occured
            return False

    def set_trace(self, n_trace=1, s_param="S21", t_format="SMITh"):
        """Set the trace that will be used for acquiring traces.

        This method configures the trace acquisition for the VNA instrument.
        The configuration is performed for a trace number wich is set to a
        S-parameter and a trace format. The method returns a Boolean value
        indicating whether the procedure was successful or not.

        Args:
            n_trace (int): number from one (1) to four (4) representing the
                trace number.
            s_param (str): S-parameter to be defined for the given trace.
                Valid S-parameters are: 'S11', 'S21', 'S21' and 'S22'.
            t_format (str): trace output format. Recommended output format
                is 'SMITh'. Other formats are available.

        Returns:
            bool: 'True' if the procedure was successful. 'False' otherwise.
        """
        # Try to write trace parameters into device
        try:

            # Set trace number and S parameter
            self.__instrument.write(
                ":SENS:TRACE" + str(n_trace) + ":SPAR " + s_param
                )

            # Set trace format
            self.__instrument.write(
                ":CALC" + str(n_trace) + ":FORM " + t_format
            )

            # Return 'True' if the procedure was executed without errors
            return True

        # Raises an exception if an error occurs
        except Vxi11Exception as vxi_trace:

            # Return 'False' if the procedure was not executed without errors
            return False

    def get_trace(self, n_trace):
        """Get trace vector in real/imaginary format.

        Ask the VNA device for the trace data. The trace consists of both real
        and imaginary values in the configured frequency values. Frequency
        data can be obtained using the 'get_freq' method from this class.

        Args:
            n_trace (int): trace number.

        Returns:
            str: string with the non-formated values of the trace. 'None' if
                an error occurs.
        """
        # Perform execution in a try/except block
        try:

            # Ask the device for current trace data
            return self.__instrument.ask(
                ":CALC" + str(n_trace) + ":DATA? SDAT"
            )

        # Handle a communication error
        except Vxi11Exception as vxi_exception:

            # Return None to tell that an error has occured.
            return None

    def get_freq(self, n_trace):
        """Get frequency vector from instrument.

        Ask the VNA device for the frequency data trace. This trace is
        generated when setting up the frequency parameters. It returns the
        frequencies vector that is matched to trace data.

        Args:
            n_trace (int): trace number.

        Returns:
            str: non-formatted string with the frequency values. 'None' if an
                error occurs.
        """
        # Perform execution in a try/except block
        try:

            # Ask the device for frequency data
            return self.__instrument.ask(
                ":SENSE" + str(n_trace) + ":FREQ:DATA?"
            )

        # Handle a communication error
        except Vxi11Exception as vxi_exception:

            # Return None to tell that an error has occured.
            return None

    @property
    def vna_connected(self):
        """VNA connection status flag attribute."""
        return self.__vna_connected

    @property
    def vna_ip(self):
        """VNA IP address attribute."""
        return self.__vna_ip
