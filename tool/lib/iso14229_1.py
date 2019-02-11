import time


class DynamicallyDefinedIdentifierArg(object):
    def __init__(self, source_data_identifier, position_in_source_data_record, memory_size):
        self.sourceDataIdentifier = source_data_identifier
        self.positionInSourceDataRecord = position_in_source_data_record
        self.memorySize = memory_size


class NegativeResponseCodes(object):
    """
    ISO-14229-1 negative response codes
    """
    POSITIVE_RESPONSE = 0x00
    # 0x01-0x0F ISO SAE Reserved
    GENERAL_REJECT = 0x10
    SERVICE_NOT_SUPPORTED = 0x11
    SUB_FUNCTION_NOT_SUPPORTED = 0x12
    INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT = 0x13
    RESPONSE_TOO_LONG = 0x14
    # 0x15-0x20 ISO SAE Reserved
    BUSY_REPEAT_REQUEST = 0x21
    CONDITIONS_NOT_CORRECT = 0x22
    # 0x23 ISO SAE Reserved
    REQUEST_SEQUENCE_ERROR = 0x24
    NO_RESPONSE_FROM_SUBNET_COMPONENT = 0x25
    FAILURE_PREVENTS_EXECUTION_OF_REQUESTED_ACTION = 0x26
    # 0x27-0x30 ISO SAE Reserved
    REQUEST_OUT_OF_RANGE = 0x31
    # 0x32 ISO SAE Reserved
    SECURITY_ACCESS_DENIED = 0x33
    # 0x34 ISO SAE Reserved
    INVALID_KEY = 0x35
    EXCEEDED_NUMBER_OF_ATTEMPTS = 0x36
    REQUIRED_TIME_DELAY_NOT_EXPIRED = 0x37
    # 0x38-0x4F Reserved by extended data link security document
    # 0x50-0x6F ISO SAE Reserved
    UPLOAD_DOWNLOAD_NOT_ACCEPTED = 0x70
    TRANSFER_DATA_SUSPENDED = 0x71
    GENERAL_PROGRAMMING_FAILURE = 0x72
    WRONG_BLOCK_SEQUENCE_COUNTER = 0x73
    # 0x74-0x77 ISO SAE Reserved
    REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING = 0x78
    # 0x79-0x7D ISO SAE Reserved
    SUB_FUNCTION_NOT_SUPPORTED_IN_ACTIVE_SESSION = 0x7E
    SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION = 0x7F
    # 0x80 ISO SAE Reserved
    RPM_TOO_HIGH = 0x81
    RPM_TOO_LOW = 0x82
    ENGINE_IS_RUNNING = 0x83
    ENGINE_IS_NOT_RUNNING = 0x84
    ENGINE_RUN_TIME_TOO_LOW = 0x85
    TEMPERATURE_TOO_HIGH = 0x86
    TEMPERATURE_TOO_LOW = 0x87
    VEHICLE_SPEED_TOO_HIGH = 0x88
    VEHICLE_SPEED_TOO_LOW = 0x89
    THROTTLE_PEDAL_TOO_HIGH = 0x8A
    THROTTLE_PEDAL_TOO_LOW = 0x8B
    TRANSMISSION_RANGE_NOT_IN_NEUTRAL = 0x8C
    TRANSMISSION_RANGE_NOT_IN_GEAR = 0x8D
    # 0x8E ISO SAE Reserved
    BRAKE_SWITCHES_NOT_CLOSED = 0x8F
    SHIFT_LEVER_NOT_IN_PARK = 0x90
    TORQUE_CONVERTER_CLUTCH_LOCKED = 0x91
    VOLTAGE_TOO_HIGH = 0x92
    VOLTAGE_TOO_LOW = 0x93
    # 0x94-0xEF Reserved for specific conditions not correct
    # 0xF0-0xFE Vehicle manufacturer specific conditions not correct
    # 0xFF ISO SAE Reserved

    NAMES = {
        0x00: "POSITIVE_RESPONSE",
        0x10: "GENERAL_REJECT",
        0x11: "SERVICE_NOT_SUPPORTED",
        0x12: "SUB_FUNCTION_NOT_SUPPORTED",
        0x13: "INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT",
        0x14: "RESPONSE_TOO_LONG",
        0x21: "BUSY_REPEAT_REQUEST",
        0x22: "CONDITIONS_NOT_CORRECT",
        0x24: "REQUEST_SEQUENCE_ERROR",
        0x25: "NO_RESPONSE_FROM_SUBNET_COMPONENT",
        0x26: "FAILURE_PREVENTS_EXECUTION_OF_REQUESTED_ACTION",
        0x31: "REQUEST_OUT_OF_RANGE",
        0x33: "SECURITY_ACCESS_DENIED",
        0x35: "INVALID_KEY",
        0x36: "EXCEEDED_NUMBER_OF_ATTEMPTS",
        0x37: "REQUIRED_TIME_DELAY_NOT_EXPIRED",
        0x70: "UPLOAD_DOWNLOAD_NOT_ACCEPTED",
        0x71: "TRANSFER_DATA_SUSPENDED",
        0x72: "GENERAL_PROGRAMMING_FAILURE",
        0x73: "WRONG_BLOCK_SEQUENCE_COUNTER",
        0x78: "REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING",
        0x7E: "SUB_FUNCTION_NOT_SUPPORTED_IN_ACTIVE_SESSION",
        0x7F: "SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION",
        0x81: "RPM_TOO_HIGH",
        0x82: "RPM_TOO_LOW",
        0x83: "ENGINE_IS_RUNNING",
        0x84: "ENGINE_IS_NOT_RUNNING",
        0x85: "ENGINE_RUN_TIME_TOO_LOW",
        0x86: "TEMPERATURE_TOO_HIGH",
        0x87: "TEMPERATURE_TOO_LOW",
        0x88: "VEHICLE_SPEED_TOO_HIGH",
        0x89: "VEHICLE_SPEED_TOO_LOW",
        0x8A: "THROTTLE_PEDAL_TOO_HIGH",
        0x8B: "THROTTLE_PEDAL_TOO_LOW",
        0x8C: "TRANSMISSION_RANGE_NOT_IN_NEUTRAL",
        0x8D: "TRANSMISSION_RANGE_NOT_IN_GEAR",
        0x8F: "BRAKE_SWITCHES_NOT_CLOSED",
        0x90: "SHIFT_LEVER_NOT_IN_PARK",
        0x91: "TORQUE_CONVERTER_CLUTCH_LOCKED",
        0x92: "VOLTAGE_TOO_HIGH",
        0x93: "VOLTAGE_TOO_LOW"
    }


class ServiceID(object):
    """
    ISO-14229-1 service ID definitions
    """
    DIAGNOSTIC_SESSION_CONTROL = 0x10
    ECU_RESET = 0x11
    CLEAR_DIAGNOSTIC_INFORMATION = 0x14
    READ_DTC_INFORMATION = 0x19
    READ_DATA_BY_IDENTIFIER = 0x22
    READ_MEMORY_BY_ADDRESS = 0x23
    READ_SCALING_DATA_BY_IDENTIFIER = 0x24
    SECURITY_ACCESS = 0x27
    COMMUNICATION_CONTROL = 0x28
    READ_DATA_BY_PERIODIC_IDENTIFIER = 0x2A
    DYNAMICALLY_DEFINE_DATA_IDENTIFIER = 0x2C
    WRITE_DATA_BY_IDENTIFIER = 0x2E
    INPUT_OUTPUT_CONTROL_BY_IDENTIFIER = 0x2F
    ROUTINE_CONTROL = 0x31
    REQUEST_DOWNLOAD = 0x34
    REQUEST_UPLOAD = 0x35
    TRANSFER_DATA = 0x36
    REQUEST_TRANSFER_EXIT = 0x37
    REQUEST_FILE_TRANSFER = 0x38
    WRITE_MEMORY_BY_ADDRESS = 0x3D
    TESTER_PRESENT = 0x3E
    ACCESS_TIMING_PARAMETER = 0x83
    SECURED_DATA_TRANSMISSION = 0x84
    CONTROL_DTC_SETTING = 0x85
    RESPONSE_ON_EVENT = 0x86
    LINK_CONTROL = 0x87
    
    NAMES = {
        0x10: "DIAGNOSTIC_SESSION_CONTROL",
        0x11: "ECU_RESET",
        0x14: "CLEAR_DIAGNOSTIC_INFORMATION",
        0x19: "READ_DTC_INFORMATION",
        0x20: "RETURN_TO_NORMAL",
        0x22: "READ_DATA_BY_IDENTIFIER",
        0x23: "READ_MEMORY_BY_ADDRESS",
        0x24: "READ_SCALING_DATA_BY_IDENTIFIER",
        0x27: "SECURITY_ACCESS",
        0x28: "COMMUNICATION_CONTROL",
        0x2A: "READ_DATA_BY_PERIODIC_IDENTIFIER",
        0x2C: "DYNAMICALLY_DEFINE_DATA_IDENTIFIER",
        0x2D: "DEFINE_PID_BY_MEMORY_ADDRESS",
        0x2E: "WRITE_DATA_BY_IDENTIFIER",
        0x2F: "INPUT_OUTPUT_CONTROL_BY_IDENTIFIER",
        0x31: "ROUTINE_CONTROL",
        0x34: "REQUEST_DOWNLOAD",
        0x35: "REQUEST_UPLOAD",
        0x36: "TRANSFER_DATA",
        0x37: "REQUEST_TRANSFER_EXIT",
        0x38: "REQUEST_FILE_TRANSFER",
        0x3D: "WRITE_MEMORY_BY_ADDRESS",
        0x3E: "TESTER_PRESENT",
        0x7F: "NEGATIVE_RESPONSE",
        0x83: "ACCESS_TIMING_PARAMETER",
        0x84: "SECURED_DATA_TRANSMISSION",
        0x85: "CONTROL_DTC_SETTING",
        0x86: "RESPONSE_ON_EVENT",
        0x87: "LINK_CONTROL"
    }


class BaseService(object):
    """Base class for services"""
    service_id = None
    #0x7F is universal negative response and is always valid
    valid_responses = [0x7F]
    SUB_FUNC_PARAM_MIN = 0x00
    SUB_FUNC_PARAM_MAX = 0x7f


class Services(object):
    """Class structure containing service specific constants, sub-function
    parameters and functions"""

    class DiagnosticSessionControl(BaseService):
        service_id = ServiceID.DIAGNOSTIC_SESSION_CONTROL
        valid_responses = [0x7F, 0x50]

        #Response Format (minus CAN-TP bytes):
        #Positive Bytes: 0x50, session_type, data1, data2, data3, data4
        #Negative Bytes: 0x7F, service_id, NRC

        class DiagnosticSessionType(object):
            # 0x00 ISO SAE Reserved
            DEFAULT_SESSION = 0x01
            PROGRAMMING_SESSION = 0x02
            EXTENDED_DIAGNOSTIC_SESSION = 0x03
            SAFETY_SYSTEM_DIAGNOSTIC_SESSION = 0x04
            # 0x05-0x3F ISO SAE Reserved
            ISO_SAE_RESERVED_MIN = 0x05
            ISO_SAE_RESERVED_MAX = 0x3F
            # 0x40-0x5F Vehicle manufacturer specific
            VEHICLE_MANUFACTURER_SESSION_MIN = 0x40
            VEHICLE_MANUFACTURER_SESSION_MAX = 0x5F
            # 0x60-0x7E System supplier specific
            SYSTEM_SUPPLIER_SESSION_MIN = 0x60
            SYSTEM_SUPPLIER_SESSION_MAX = 0x7E
            # 0x7F ISO SAE Reserved
            def is_valid_session(self, sub_function):
                """Returns True if 'sub_function' is a valid session type and
                False otherwise"""
                #Strip off the MSB which is used as flag to suppress responses
                #so we don't care what it is
                sub_function = 0x7f & sub_function
                if (sub_function is self.DEFAULT_SESSION
                    or sub_function is self.PROGRAMMING_SESSION
                    or sub_function is self.EXTENDED_DIAGNOSTIC_SESSION
                    or sub_function is self.SAFETY_SYSTEM_DIAGNOSTIC_SESSION
                    or(sub_function <= self.VEHICLE_MANUFACTURER_SESSION_MAX and
                        sub_function >= self.VEHICLE_MANUFACTURER_SESSION_MIN)
                    or(sub_function <= self.SYSTEM_SUPPLIER_SESSION_MAX and
                        sub_function >= self.SYSTEM_SUPPLIER_SESSION_MIN)):
                    return True
                else:
                    return False

            NAMES = {
                0x01: "DEFAULT_SESSION",
                0x02: "PROGRAMMING_SESSION",
                0x03: "EXTENDED_DIAGNOSTIC_SESSION",
                0x04: "SAFETY_SYSTEM_DIAGNOSTIC_SESSION"
            }
            def get_name(self, sub_function):
                #wipe out the suppress response bit from the passed in sub_function
                sub_function = sub_function & 0x7f
                if (sub_function == 0x00 or sub_function == 0x7F or 
                        (sub_function <= self.ISO_SAE_RESERVED_MAX and 
                        sub_function >= self.ISO_SAE_RESERVED_MIN)):
                    return "!!ISO_SAE_RESERVED!!"
                elif (sub_function <= self.VEHICLE_MANUFACTURER_SESSION_MAX and
                        sub_function >= self.VEHICLE_MANUFACTURER_SESSION_MIN):
                    return "VEHICLE_MANUFACTURER_SESSION".format(sub_function)
                elif (sub_function <= self.SYSTEM_SUPPLIER_SESSION_MAX and 
                        sub_function >= self.SYSTEM_SUPPLIER_SESSION_MIN):
                    return "SYSTEM_SUPPLIER_SESSION".format(sub_function)
                else:
                    return self.NAMES.get(sub_function, "!!UNKNOWN_SESSION_TYPE!!")

    class EcuReset(BaseService):
        service_id = ServiceID.ECU_RESET
        valid_responses = [0x7F, 0x51]
        
        class ResetType(object):
            # 0x00 ISO SAE Reserved
            HARD_RESET = 0x01
            KEY_OFF_ON_RESET = 0x02
            SOFT_RESET = 0x03
            ENABLE_RAPID_POWER_SHUTDOWN = 0x04
            DISABLE_RAPID_POWER_SHUTDOWN = 0x05
            # 0x06-0x3F ISO SAE Reserved
            # 0x40-0x5F Vehicle manufacturer specific
            # 0x60-0x7E System supplier specific
            # 0x7F ISO SAE Reserved

    class SecurityAccess(BaseService):
        service_id = ServiceID.SECURITY_ACCESS
        valid_responses = [0x7f, 0x67]

        class RequestSeedOrSendKey(object):
            """
            These are lined up so that value X "request seed level N" has a matching "send key level N" at value X+1.

            0x01 is Request seed level 0x01
            0x02 is Send key level 0x01
            0x03 is Request seed level 0x02
            0x04 is Send key level 0x02
            (...)
            0x41 is Request seed level 0x21
            0x42 is Send key level 0x21

            The security levels numbering is arbitrary and does not imply any relationship between the levels.
            """

            # 0x00 ISO SAE Reserved
            # 0x01-0x42 Vehicle manufacturer specific request seed/send key pairs
            # 0x43-0X5E ISO SAE Reserved
            ISO_26021_2_VALUES = 0x5F
            ISO_26021_2_SEND_KEY = 0x60
            # 0x61-0x7E System supplier specific
            # 0x7F ISO SAE Reserved

            __REQUEST_SEED_MIN = 0x01
            __REQUEST_SEED_MAX = 0x41
            __SEND_KEY_MIN = 0x02
            __SEND_KEY_MAX = 0x42

            def is_valid_request_seed_level(self, sub_function):
                """Returns True if 'sub_function' is a valid request seed value and False otherwise"""
                value = sub_function & 0x7F
                valid_interval = self.__REQUEST_SEED_MIN <= value <= self.__REQUEST_SEED_MAX
                is_odd = value % 2 == 1
                return valid_interval and is_odd

            def is_valid_send_key_level(self, sub_function):
                """Returns True if 'sub_function' is a valid send key value and False otherwise"""
                value = sub_function & 0x7F
                valid_interval = self.__SEND_KEY_MIN <= value <= self.__SEND_KEY_MAX
                is_even = value % 2 == 0
                return valid_interval and is_even

            @staticmethod
            def get_send_key_for_request_seed(seed):
                return seed + 1

    class TesterPresent(BaseService):
        service_id = ServiceID.TESTER_PRESENT
        valid_responses = [0x7F, 0x7E] 

class Constants(object):
    # NR_SI (Negative Response Service Identifier) is a bit special, since it is not a service per se.
    # From ISO-14229-1 specification: "The NR_SI value is co-ordinated with the SI values. The NR_SI
    # value is not used as a SI value in order to make A_Data coding and decoding easier."
    NR_SI = 0x7F


class Iso14229_1(object):
    P3_CLIENT = 5

    def __init__(self, tp):
        self.tp = tp

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @staticmethod
    def get_service_response_id(identifier):
        """
        Returns the service response ID for 'identifier'

        :param identifier: Identifier
        :return: Service response ID for 'identifier'
        """
        return identifier + 0x40

    def send_request(self, data):
        """
        Sends a request message containing 'data' through the underlying TP layer

        :param data: The data to send
        :return: None
        """
        return self.tp.send_request(data)

    def send_response(self, data):
        """
        Sends a response message containing 'data' through the underlying TP layer

        :param data: The data to send
        :return: None
        """
        return self.tp.send_response(data)

    def receive_response(self, wait_window):
        """
        Attempts to receive a response through the underlying TP layer

        :param wait_window: Minimum time (in seconds) to wait before timeout
        :return: The received response if successful,
                 None otherwise
        """
        start_time = time.clock()
        while True:
            current_time = time.clock()
            if (current_time - start_time) > wait_window:
                return None

            response = self.tp.indication(wait_window)
            if response is not None and len(response) > 3:
                if response[0] == Constants.NR_SI and \
                        response[2] == NegativeResponseCodes.REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING:
                    continue
            break
        return response

    @staticmethod
    def is_positive_response(response):
        """
        Returns a bool indicating whether 'response' is positive

        :param response: Response data after CAN-TP layer has been removed
        :return: False if response is a NEGATIVE_RESPONSE,
                 True otherwise
        """
        if response is not None and len(response) > 0 and response[0] != Constants.NR_SI:
            return True
        return False

    def read_data_by_identifier(self, identifier):
        """
        Sends a "read data by identifier" request for 'identifier'

        :param identifier: Data identifier
        :return: Response data if successful,
                 None otherwise
        """
        response = []
        num_dids = len(identifier)
        if num_dids > 0:
            request = [0] * ((num_dids * 2) + 1)
            request[0] = ServiceID.READ_DATA_BY_IDENTIFIER
            for i in range(0, num_dids):
                request[i * 2 + 1] = (identifier[i] >> 8) & 0xFF
                request[i * 2 + 2] = identifier[i] & 0xFF
            self.tp.send_request(request)
            response = self.receive_response(self.P3_CLIENT)
        return response

    def read_memory_by_address(self, address_and_length_format, memory_address, memory_size):
        """
        Sends a "read memory by address" request for 'memory_address'

        :param address_and_length_format: Address and length format
        :param memory_address: Memory address
        :param memory_size: Memory size
        :return: Response data if successful,
                 None otherwise
        """
        address_size_format = (address_and_length_format >> 4) & 0xF
        data_size_format = (address_and_length_format & 0xF)

        request = [0] * (1 + 1 + address_size_format + data_size_format)
        request[0] = ServiceID.READ_MEMORY_BY_ADDRESS
        request[1] = address_and_length_format
        offset = 2
        for i in (range(0, address_size_format)):
            request[address_size_format + offset - i - 1] = (memory_address & 0xFF)
            memory_address = (memory_address >> 8)

        offset += address_size_format

        for i in (range(0, data_size_format)):
            request[data_size_format + offset - i - 1] = (memory_size & 0xFF)
            memory_size = (memory_size >> 8)

        self.tp.send_request(request)
        response = self.receive_response(self.P3_CLIENT)

        return response

    def write_memory_by_address(self, address_and_length_format, memory_address, memory_size, data):
        """
        Sends a "write memory by address" request to write 'data' to 'memory_address'

        :param address_and_length_format: Address and length format
        :param memory_address: Memory address
        :param memory_size: Memory size
        :param data: The data to write to 'memory_address'
        :return: Response data if successful,
                 None otherwise
        """
        address_size_format = (address_and_length_format >> 4) & 0xF
        data_size_format = (address_and_length_format & 0xF)

        request = [0] * (1 + 1 + address_size_format + data_size_format)
        request[0] = ServiceID.WRITE_MEMORY_BY_ADDRESS
        request[1] = address_and_length_format
        offset = 2
        for i in (range(0, address_size_format)):
            request[address_size_format + offset - i - 1] = (memory_address & 0xFF)
            memory_address = (memory_address >> 8)

        offset += address_size_format

        for i in (range(0, data_size_format)):
            request[data_size_format + offset - i - 1] = (memory_size & 0xFF)
            memory_size = (memory_size >> 8)

        request += data
        self.tp.send_request(request)
        response = self.receive_response(self.P3_CLIENT)

        return response

    def write_data_by_identifier(self, identifier, data):
        """
        Sends a "write data by identifier" request to write 'data' to 'identifier'

        :param identifier: Data identifier
        :param data: Data to write to 'identifier'
        :return: Response data if successful,
                 None otherwise
        """
        request = [0] * (1 + 2)

        request[0] = ServiceID.WRITE_DATA_BY_IDENTIFIER
        request[1] = (identifier >> 8) & 0xFF
        request[2] = identifier & 0xFF
        request += data
        self.tp.send_request(request)
        response = self.receive_response(self.P3_CLIENT)

        return response

    def input_output_control_by_identifier(self, identifier, data):
        """
        Sends a "input output control by identifier" request for 'data' to 'identifier'

        :param identifier: Data identifier
        :param data: Data
        :return: Response data if successful,
                 None otherwise
        """
        request = [0] * (1 + 2)

        request[0] = ServiceID.INPUT_OUTPUT_CONTROL_BY_IDENTIFIER
        request[1] = (identifier >> 8) & 0xFF
        request[2] = identifier & 0xFF
        request += data

        self.tp.send_request(request)
        response = self.receive_response(self.P3_CLIENT)

        return response

    def dynamically_define_data_identifier(self, identifier, sub_function, sub_function_arg):
        """
        Sends a "dynamically define data identifier" request for 'identifier'

        :param identifier: DDDID to set
        :param sub_function: Sub function
        :param sub_function_arg: Sub function arguments
        :return: Response data if successful,
                 None otherwise
        """
        if identifier is None or sub_function is None or sub_function_arg is None:
            return None

        request = [0] * (1 + 1 + 2 + len(sub_function_arg) * 4)
        request[0] = ServiceID.DYNAMICALLY_DEFINE_DATA_IDENTIFIER
        request[1] = sub_function
        request[2] = (identifier >> 8) & 0xFF
        request[3] = identifier & 0xFF

        offset = 4
        for did in sub_function_arg:
            request[offset + 0] = (did.sourceDataIdentifier >> 8) & 0xFF
            request[offset + 1] = did.sourceDataIdentifier & 0xFF
            request[offset + 2] = did.positionInSourceDataRecord
            request[offset + 3] = did.memorySize
            offset += 4

        self.tp.send_request(request)
        response = self.receive_response(self.P3_CLIENT)

        return response

    def diagnostic_session_control(self, session_type):
        """
        Sends a "DiagnosticSessionControl" request for specified session type

        :param session_type: Indicates which kind of session should be requested
        :return: Response data if successful,
                 None otherwise
        """
        request = [0] * 2
        request[0] = ServiceID.DIAGNOSTIC_SESSION_CONTROL
        request[1] = session_type

        self.tp.send_request(request)
        response = self.receive_response(self.P3_CLIENT)

        return response


    def ecu_reset(self, reset_type):
        """
        Sends an "ECU reset" request for specified reset type

        :param reset_type: Indicates which kind of reset should be requested
        :return: Response data if successful,
                 None otherwise
        """
        request = [0] * 2
        request[0] = ServiceID.ECU_RESET
        request[1] = reset_type

        self.tp.send_request(request)
        response = self.receive_response(self.P3_CLIENT)

        return response

    def security_access_request_seed(self, level, data_record=None):
        """
        Sends a Security Access "Request seed" message for 'level'

        :param level: Security Access Type level to send request seed for
        :param data_record: Optional data to transmit when requesting seed, e.g. client identification
        :return: Response data (containing seed) if successful,
                 None otherwise
        """
        service_id = ServiceID.SECURITY_ACCESS
        request = [service_id, level]
        if data_record:
            for data_record in data_record:
                request.append(data_record)

        self.tp.send_request(request)
        response = self.receive_response(self.P3_CLIENT)

        return response

    def security_access_send_key(self, level, key):
        """
        Sends a Security Access "Send key" message with 'key' for 'level'

        :param level: Security Access Type level to send key for
        :param key: Key to transmit
        :return: Response data if successful,
                 None otherwise
        """
        service_id = ServiceID.SECURITY_ACCESS
        request = [service_id, level]
        for key_byte in key:
            request.append(key_byte)

        self.tp.send_request(request)
        response = self.receive_response(self.P3_CLIENT)

        return response

    def read_data_by_periodic_identifier(self, transmission_mode, identifier):
        """
        Sends a "read data by periodic identifier" request for 'identifier'

        :param transmission_mode: Transmission mode
        :param identifier: Identifier
        :return: Response data if successful,
                 None otherwise
        """
        if transmission_mode is None or identifier is None or len(identifier) == 0:
            return None

        request = [0] * (2 + len(identifier))
        request[0] = ServiceID.READ_DATA_BY_PERIODIC_IDENTIFIER
        request[1] = transmission_mode

        for i in range(0, len(identifier)):
            request[2 + i] = identifier[i]

        self.tp.send_request(request)
        response = self.receive_response(self.P3_CLIENT)

        return response
