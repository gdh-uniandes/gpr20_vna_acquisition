"""ROS interface for the VNA acquisition utility."""

import rospy
from gpr20_vna_acquisition.vna_driver import VNADriver
from gpr20_msgs.srv import VNAGetData, VNAGetDataResponse
from gpr20_msgs.srv import VNAGetFreq, VNAGetFreqResponse
from gpr20_msgs.srv import VNASweepSetup, VNASweepSetupResponse
from gpr20_msgs.srv import VNAConnection, VNAConnectionResponse
from gpr20_msgs.srv import VNACalibrationStatus, VNACalibrationStatusResponse


class VNANode(object):
    """VNA acquisition ROS interface for GPR-20 robot.

    This class provides the ROS interface from the software architecture to the
    Vector Network Analyzer (VNA) device used in the robot. The interface
    consists of four services user for connecting and disconnecting the
    device, setting up the frequency sweep parameters, getting the frequencies
    vector and the trace itself.

    Attributes:
        vna_driver (VNADriver): instance of the driver class for handling the
            VNA requests.
    """

    def __init__(self):
        """Initialize the VNA ROS interface class."""
        # Initialize the ROS node
        rospy.init_node("vna_acquisition", anonymous=False)

        # Create the connection service for VNA device
        rospy.Service(
            "vna_connection",
            VNAConnection,
            self.__connection_handler
        )

        # Create the check calibration status for VNA device
        rospy.Service(
            "vna_get_calibration_status",
            VNACalibrationStatus,
            self.__get_calibration_status_handler
        )

        # Create the frequency sweep setup service
        rospy.Service(
            "vna_freq_sweep_setup",
            VNASweepSetup,
            self.__freq_sweep_setup_handler
        )

        # Create the service for acquiring the frequency vector
        rospy.Service(
            "vna_get_freq",
            VNAGetFreq,
            self.__get_freq_data_handler
        )

        # Create the service for acquiring data
        rospy.Service(
            "vna_get_data",
            VNAGetData,
            self.__get_vna_data_handler
        )

        # Creates an instance of vna node
        self.__vna_driver = VNADriver()

        # Keeps node alive
        rospy.spin()

    def __connection_handler(self, srv):
        """Handle the connection and disconnection for VNA device.

        This handler processes the request to connect/disconnect the VNA
        to/from the GPR-20 software stack. The required parameter for the
        connection is the VNA IP address.

        Args:
            srv (gpr20_msgs.srv.VNAConnection): message with the connection
                type and the IP address.

        Returns:
            gpr20_msgs.srv.VNAConnectionResponse: response with boolean flag
                indicating if process was successful or not.
        """
        # Connects to VNA if connection flag is set
        if srv.connection:
            status = self.__vna_driver.connect_to_vna(srv.ip_addr)[0]

        # Disconnects from VNA if connection flag is unset
        else:
            status = self.__vna_driver.disconnect_from_vna()

        # Returns the empty response
        return VNAConnectionResponse(status)

    def __get_calibration_status_handler(self, srv):
        """Handle the calibration status check request for VNA device.

        Args:
            srv (gpr20_msgs.srv.VNACalibrationStatus): empty service request
                for checking the VNA device calibration status.

        Returns:
            gpr20_msgs.srv.VNACalibrationStatusResponse: response with the
                calibration status as an integer value.
        """
        # Check the calibration status in the device
        cal_status = self.__vna_driver.check_calibration_status()

        # Return the service response
        return VNACalibrationStatusResponse(cal_status)

    def __freq_sweep_setup_handler(self, srv):
        """Handle the frequency sweep setup for VNA device.

        Args:
            srv (gpr20_msgs.srv.VNASweepSetup): service with the frequency
                sweep parameters.

        Returns:
            gpr20_msgs.srv.VNASweepResponse: response with boolean flag
                indicating if process was successful or not.
        """
        # Checks that number of points is valid (0-4000)
        if srv.freq_points < 0 or srv.freq_points > 4000:
            return VNASweepSetupResponse(False)

        # Checks that stop frequency is valid (>0)
        if srv.freq_stop < 0:
            return VNASweepSetupResponse(False)

        # Checks that start frequency is valid (0-stop)
        if srv.freq_start > srv.freq_stop or srv.freq_stop < 0:
            return VNASweepSetupResponse(False)

        # Calls the method in driver to setup pararmeters
        status = self.__vna_driver.set_frequency_sweep(
            srv.freq_start,
            srv.freq_stop,
            srv.freq_points
        )

        # Set the trace with the default configuration
        self.__vna_driver.set_trace()

        # Returns false to indicate that parameters were configured properly
        return VNASweepSetupResponse(status)

    def __get_vna_data_handler(self, srv):
        """Handle a request for the trace data vector from VNA device.

        Args:
            srv (gpr20_msgs.srv.VNAGetData): service request. The request is
                empty since no parameters are required to get the trace.

        Attribute:
            gpr20_msgs.srv.VNAGetDataResponse: response for service. Includes
                a flag and the trace data. The trace data is either full or
                empty. The flag is set as True if procedure was successful.
                False otherwise.
        """
        # Retrieve the trace data
        data = self.__vna_driver.get_trace(1)

        # Check acquired data
        if data is not None:

            # Return service response with data
            return VNAGetDataResponse(True, data)

        # Execute block if data is 'None'
        else:

            # Return an empty value to indicate an error
            return VNAGetDataResponse(False, "")

    def __get_freq_data_handler(self, srv):
        """Handle a request for the frequency vector from VNA device.

        Args:
            srv (gpr20_msgs.srv.VNAGetFreq): request for the VNA frequency
                request.

        Returns:
            gpr20_msgs.srv.VNAGetFreqResponse: response that includes the
                requested frequency vector.
        """
        # Get frequency data from VNA instrument
        freq_data = self.__vna_driver.get_freq(1)

        # Define status based on response
        status = True if freq_data is not None else False

        # Check if status is 'False'
        if not status:

            # Convert frequency data to empty string
            freq_data = ""

        # Returns frequency data
        return VNAGetFreqResponse(status, freq_data)

    def __del__(self):
        """Execute on instance deletion."""
        rospy.loginfo("Node is dead")
