from __future__ import print_function
from lib.can_actions import auto_blacklist
from lib.common import list_to_hex_str, parse_int_dec_or_hex
from lib.constants import ARBITRATION_ID_MAX, ARBITRATION_ID_MAX_EXTENDED, ARBITRATION_ID_MIN
from lib.iso15765_2 import IsoTp
from lib.iso14229_1 import Iso14229_1, NegativeResponseCodes, Services, ServiceID, BaseService, InputOutputControlParameters
from sys import stdout, version_info
import argparse
import datetime
import time
import itertools as it

# Handle large ranges efficiently in both python 2 and 3
if version_info[0] == 2:
    range = xrange

UDS_SERVICE_NAMES = {
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

NRC_NAMES = {
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

DELAY_DISCOVERY = 0.01
DELAY_TESTER_PRESENT = 0.5
TIMEOUT_SERVICES = 0.2

# Max number of arbitration IDs to backtrack during verification
VERIFICATION_BACKTRACK = 5
# Extra time in seconds to wait for responses during verification
VERIFICATION_EXTRA_DELAY = 0.5

BYTE_MIN = 0x00
BYTE_MAX = 0xFF


def uds_discovery(min_id, max_id, blacklist_args, auto_blacklist_duration, delay, verify, print_results=True):
    """Scans for diagnostics support by brute forcing session control messages to different arbitration IDs.
    Returns a list of all (client_arb_id, server_arb_id) pairs found.

    :param min_id: start arbitration ID value
    :param max_id: end arbitration ID value
    :param blacklist_args: blacklist for arbitration ID values
    :param auto_blacklist_duration: seconds to scan for interfering arbitration IDs to blacklist automatically
    :param delay: delay between each message
    :param verify: whether found arbitration IDs should be verified
    :param print_results: whether results should be printed to stdout
    :type min_id: int
    :type max_id: int
    :type blacklist_args: [int]
    :type auto_blacklist_duration: float
    :type delay: float
    :type verify: bool
    :type print_results: bool
    :return: list of (client_arbitration_id, server_arbitration_id) pairs
    :rtype [(int, int)]
    """
    # Set defaults
    if min_id is None:
        min_id = ARBITRATION_ID_MIN
    if max_id is None:
        if min_id <= ARBITRATION_ID_MAX:
            max_id = ARBITRATION_ID_MAX
        else:
            # If min_id is extended, use an extended default max_id as well
            max_id = ARBITRATION_ID_MAX_EXTENDED
    if auto_blacklist_duration is None:
        auto_blacklist_duration = 0
    if blacklist_args is None:
        blacklist_args = []

    # Sanity checks
    if max_id < min_id:
        raise ValueError("max_id must not be smaller than min_id - got min:0x{0:x}, max:0x{1:x}".format(min_id, max_id))
    if auto_blacklist_duration < 0:
        raise ValueError("auto_blacklist_duration must not be smaller than 0, got {0}'".format(auto_blacklist_duration))

    service_id = Services.DiagnosticSessionControl.service_id
    sub_function = Services.DiagnosticSessionControl.DiagnosticSessionType.DEFAULT_SESSION
    session_control_data = [service_id, sub_function]

    def is_valid_response(message):
        return len(message.data) >= 2 and message.data[1] in Services.DiagnosticSessionControl.valid_responses

    found_arbitration_ids = []

    with IsoTp(None, None) as tp:
        blacklist = set(blacklist_args)
        # Perform automatic blacklist scan
        if auto_blacklist_duration > 0:
            auto_blacklist_arb_ids = auto_blacklist(tp.bus, auto_blacklist_duration, is_valid_response, print_results)
            blacklist |= auto_blacklist_arb_ids

        # Prepare session control frame
        session_control_frames = tp.get_frames_from_message(session_control_data)
        send_arbitration_id = min_id - 1
        while send_arbitration_id < max_id:
            send_arbitration_id += 1
            if print_results:
                print("\rSending Diagnostic Session Control to 0x{0:04x}".format(send_arbitration_id), end="")
                stdout.flush()
            # Send Diagnostic Session Control
            tp.transmit(session_control_frames, send_arbitration_id, None)
            end_time = time.time() + delay
            # Listen for response
            while time.time() < end_time:
                msg = tp.bus.recv(0)
                if msg is None:
                    # No response received
                    continue
                if msg.arbitration_id in blacklist:
                    # Ignore blacklisted arbitration IDs
                    continue
                if is_valid_response(msg):
                    # Valid response
                    if verify:
                        # Verification - backtrack the latest IDs and verify that the same response is received
                        verified = False
                        # Set filter to only receive messages for the arbitration ID being verified
                        tp.set_filter_single_arbitration_id(msg.arbitration_id)
                        if print_results:
                            print("\n  Verifying potential response from 0x{0:04x}".format(send_arbitration_id))
                        verify_id_range = range(send_arbitration_id, send_arbitration_id - VERIFICATION_BACKTRACK, -1)
                        for verification_arbitration_id in verify_id_range:
                            if print_results:
                                print("    Resending 0x{0:0x}... ".format(verification_arbitration_id), end=" ")
                            tp.transmit(session_control_frames, verification_arbitration_id, None)
                            # Give some extra time for verification, in case of slow responses
                            verification_end_time = time.time() + delay + VERIFICATION_EXTRA_DELAY
                            while time.time() < verification_end_time:
                                verification_msg = tp.bus.recv(0)
                                if verification_msg is None:
                                    continue
                                if is_valid_response(verification_msg):
                                    # Verified
                                    verified = True
                                    # Update send ID - if server responds slowly, the initial value may be faulty.
                                    # It also ensures we resume searching on the next arbitration ID after the actual
                                    # match, rather than the one after the last potential match (which could lead to
                                    # false negatives if multiple servers listen to adjacent arbitration IDs and respond
                                    # slowly)
                                    send_arbitration_id = verification_arbitration_id
                                    break
                            if print_results:
                                # Print result
                                if verified:
                                    print("Success")
                                else:
                                    print("No response")
                            if verified:
                                # Verification succeeded - stop checking
                                break
                        # Remove filter after verification
                        tp.clear_filters()
                        if not verified:
                            # Verification failed - move on
                            if print_results:
                                print("  False match - skipping")
                            continue
                    if print_results:
                        if not verify:
                            # Blank line needed
                            print()
                        print("Found diagnostics server listening at 0x{0:04x}, response at 0x{1:04x}".format(
                            send_arbitration_id, msg.arbitration_id))
                    # Add found arbitration ID pair
                    found_arb_id_pair = (send_arbitration_id, msg.arbitration_id)
                    found_arbitration_ids.append(found_arb_id_pair)
        if print_results:
            print()
    return found_arbitration_ids


def __uds_discovery_wrapper(args):
    """Wrapper used to initiate a UDS discovery scan"""
    min_id = args.min
    max_id = args.max
    blacklist = args.blacklist
    auto_blacklist_duration = args.autoblacklist
    delay = args.delay
    verify = not args.skipverify
    print_results = True

    try:
        arb_id_pairs = uds_discovery(min_id, max_id, blacklist, auto_blacklist_duration, delay, verify, print_results)
        if len(arb_id_pairs) == 0:
            # No UDS discovered
            print("\nDiagnostics service could not be found.")
        else:
            # Print result table
            print("\nIdentified diagnostics:\n")
            table_line = "+------------+------------+"
            print(table_line)
            print("| CLIENT ID  | SERVER ID  |")
            print(table_line)
            for (client_id, server_id) in arb_id_pairs:
                print("| 0x{0:08x} | 0x{1:08x} |".format(client_id, server_id))
            print(table_line)
    except ValueError as e:
        print("Discovery failed: {0}".format(e))


def service_discovery(arb_id_request, arb_id_response, timeout, min_id=BYTE_MIN, max_id=BYTE_MAX,
                      print_results=True):
    """Scans for supported UDS services on the specified arbitration ID. Returns a list of found service IDs.

    :param arb_id_request: arbitration ID for requests
    :param arb_id_response: arbitration ID for responses
    :param timeout: delay between each request sent
    :param min_id: first service ID to scan
    :param max_id: last service ID to scan
    :param print_results: whether progress should be printed to stdout
    :type arb_id_request: int
    :type arb_id_response: int
    :type timeout: float
    :type min_id: int
    :type max_id: int
    :type print_results: bool
    :return: list of supported service IDs
    :rtype [int]
    """
    found_services = []

    with IsoTp(arb_id_request=arb_id_request, arb_id_response=arb_id_response) as tp:
        # Setup filter for incoming messages
        tp.set_filter_single_arbitration_id(arb_id_response)
        # Send requests
        try:
            for service_id in range(min_id, max_id + 1):
                tp.send_request([service_id])
                if print_results:
                    print("\rProbing service 0x{0:02x} ({0}/{1}): found {2}".format(
                        service_id, max_id, len(found_services)), end="")
                stdout.flush()
                # Get response
                msg = tp.bus.recv(timeout)
                if msg is None:
                    # No response received
                    continue
                # Parse response
                if len(msg.data) > 3:
                    # Since service ID is included in the response, mapping is correct even if response is delayed
                    service_id = msg.data[2]
                    status = msg.data[3]
                    if status != NegativeResponseCodes.SERVICE_NOT_SUPPORTED:
                        # Any other response than "service not supported" counts
                        found_services.append(service_id)
            if print_results:
                print("\nDone!\n")
        except KeyboardInterrupt:
            if print_results:
                print("\nInterrupted by user!\n")
    return found_services


def __service_discovery_wrapper(args):
    """Wrapper used to initiate a service discovery scan"""
    arb_id_request = args.src
    arb_id_response = args.dst
    timeout = args.timeout
    # Probe services
    found_services = service_discovery(arb_id_request, arb_id_response, timeout)
    # Print results
    for service_id in found_services:
        service_name = UDS_SERVICE_NAMES.get(service_id, "Unknown service")
        print("Supported service 0x{0:02x}: {1}".format(service_id, service_name))


def __service_scan_wrapper(args):
    """Wrapper used to initiate a supported service scan"""
    arb_id_request = args.src
    arb_id_response = args.dst
    service_id = args.service
    timeout = args.timeout
    is_oem = args.oem
    is_safety = args.saf
    is_supplier = args.sss
    min_id = args.min
    max_id = args.max
    try:
        #Services available to defaultSession: SessionControl; ECUReset; TesterPresent; ResponseOnEvent; ReadDID; ReadMemory; ReadScalingData; DynamicallyDefineDID; WriteDID; WriteMemory; ClearDiagnosticInfo; ReadDTCInfo; RoutineControl.
        if service_id == Services.DiagnosticSessionControl.service_id:
            found_sub_funcs = scan_session_control(arb_id_request, arb_id_response, timeout)
            # Print results
            if found_sub_funcs:
                for sub_func in found_sub_funcs:
                    session_type = Services.DiagnosticSessionControl.DiagnosticSessionType().get_name(sub_func)
                    print("Supported service (0x{0:02x}) sub-function 0x{1:02x}: {2}".format(service_id, sub_func, session_type))
        elif service_id == ServiceID.WRITE_MEMORY_BY_ADDRESS:
            #First find all applicable "addressAndLengthFormatIdentifier"
                #Do this by purposely triggering NRC 0x13 by improper total length (e.g. leave off data bytes)
                #There are 4-bits for address and length sizes
            #Then for each addressAndLengthFormatIdentifier, try all memory ranges
            #record NRC
            #print table of memory with NRCs labeled
            #valid_memory_write
            service_name = ServiceID.NAMES.get(service_id, "Unknown service")
            print("Service 0x{0:02x}: {1} not supported at this time...".format(service_id, service_name))
        elif service_id == ServiceID.ROUTINE_CONTROL:
            print("Routine Control Scan")
            #TODO : Add safety ranges for routine control
            routine_map = scan_routine_control(arb_id_request, arb_id_response, timeout, is_oem, is_supplier, min_id, max_id)
            if routine_map:
                for item in routine_map:
                    print("Routine 0x{0:02x} : {1}".format(item[0], item[1]))
            else:
                print("No supported routines found in scan")

        else:
            service_name = ServiceID.NAMES.get(service_id, "Unknown service")
            print("Service 0x{0:02x}: {1} not supported at this time...".format(service_id, service_name))

        '''elif service_id == Services.
        TODO: Add check to direct users to services_scan_ext command
        '''
    except ValueError as e:
        print("\nService Scan failed: {0}".format(e))


def __ext_service_scan_wrapper(args):
    """Wrapper used to initiate a supported extended service scan"""
    arb_id_request = args.src
    arb_id_response = args.dst
    service = args.service
    timeout = args.timeout
    is_oem = args.oem
    is_supplier = args.sss
    is_safety = args.saf
    min_id = args.min
    max_id = args.max
    try:
        #Set to extended mode
        response = extended_session(arb_id_request, arb_id_response)
        if not Iso14229_1.is_positive_response(response):
            raise ValueError("Unable to enter extended session")
        else:
            print("Entered extended session")

        if service == Services.InputOutputControlByIdentifier.service_id:
            found_iocontrols = scan_io_controls(arb_id_request, arb_id_response,
                 timeout, is_oem, is_supplier, is_safety, min_id, max_id)
            if found_iocontrols:
                print("")
                for item in found_iocontrols:
                    print("IO Control DID 0x{0:02x} : {1}".format(item[0], item[1]))

        '''elif service == Services.
        TODO: Add check to output help / direct users to services_scan command
        '''
    except ValueError as e:
        print("\n Extended Service Scan failed: {0}".format(e))

def scan_io_controls(arb_id_request, arb_id_response, timeout=None,
        is_oem=False, is_supplier=False, is_safety=None, min_id=None, 
        max_id=None, print_results=True):
    """
    Uses DIDs.
        OEM - 0x0100 - 0xA5FF; 0xA800 - 0xACFF; 0xB000 - 0xB1FF; 0xC2000 - 0xC2FF; 0xCF00 - 0xEFFF; 
        SAF - 0xFA00 - 0xFA0F (airbags); 0xFA19 - 0xFAFF
        SSS - 0xFD00 - 0xFEFF
    """
    io_control_list = []
    id_scan_range = list(make_did_range(is_oem, is_supplier, is_safety, min_id, max_id))
    last_scanned_did = None

    with IsoTp(arb_id_request=arb_id_request, arb_id_response=arb_id_response) as tp:
        tp.set_filter_single_arbitration_id(arb_id_response)
        with Iso14229_1(tp) as uds:
            if timeout is not None:
                uds.P3_CLIENT = timeout
            try:
                idx = 0
                for did in id_scan_range:
                    idx += 1
                    if print_results:
                        print("\rProbing service 0x{0:02x} data ID"
                                " 0x{1:02x} ({2}/{3})".format(
                                ServiceID.INPUT_OUTPUT_CONTROL_BY_IDENTIFIER, 
                                did, idx, len(id_scan_range)), end="")

                        stdout.flush()

                    #Start with no controlMask, but need to guess for correct controlMask size (all 1's)
                    ## controlMask is one or many bytes.
                    ### Start with 0, for every NRC 0x13, increase by 1 byte until not NRC 0x13.
                    # DONE __ BAD_LENGTH (0x13) indicates a retry.
                    # DONE __ NOT_SUPPORTED (0x31) indicates not supported.
                    # DONE __ Security check indicates security enabled, and supported
                    # DONE __ Positive response indicates supported, no security
                    # DONE __ Other NRCs indicate supported.
                    controlOptionRecord = [InputOutputControlParameters.RETURN_CONTROL_TO_ECU]
                    controlEnableMaskRecord = []
		
                    #Arbitrarily picked 10; this could be lower or higher
                    retry_count = 10 
                    while retry_count > 0:
                        #TODO : Report to user how big the controlEnableMaskRecord is
                        response = uds.input_output_control_by_identifier(did,
                                    controlOptionRecord, controlEnableMaskRecord) 
                        if response is None:
                            response = uds.input_output_control_by_identifier(did,
                                        controlOptionRecord, controlEnableMaskRecord) 
                        if Iso14229_1.is_positive_response(response):
                            io_control_list.append([did, "SUPPORTED_NO_SECURITY"])
                            retry_count = 0
                        elif response is None:
                                retry_count = 0
                                pass
                        else:
                            if response[2] is NegativeResponseCodes.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT:
                                #Increase controlEnableMaskRecord and RETRY 
                                controlEnableMaskRecord += [0xff]
                                retry_count -= 1
                            elif response[2] is NegativeResponseCodes.REQUEST_OUT_OF_RANGE:
                                #Do nothing. Not supported.
                                retry_count = 0
                                pass
                            elif response[2] is NegativeResponseCodes.SECURITY_ACCESS_DENIED:
                                io_control_list.append([did, "SUPPORTED_SECURITY_ACCESS_DENIED"])
                                retry_count = 0
                            else:
                                io_control_list.append([did, "SUPPORTED_NO_SECURITY"])
                                retry_count = 0
                    last_scanned_did = did
            except KeyboardInterrupt:
                if print_results:
                    print("\nInterrupted by user!")
                    if last_scanned_did is not None:
                        print("\nLast scanned DID : {0:02x}".format(did))

    return io_control_list

def make_did_range(is_oem, is_supplier, is_safety, min_id=None, max_id=None):
    id_range = []
    if is_oem:
        print("Scanning OEM ranges: \n\t0x0100 - 0xa5ff"
                "\n\t0xa800 - 0xacff\n\t0xb000 - 0xb1ff"
                "\n\t0xc200 - 0xc2ff\n\t0xcf00 - 0xefff")
        id_range = it.chain(range(0x0100, 0xA5FF+1), 
                range(0xA800, 0xACFF+1), range(0xB000, 0xB1FF+1), 
                range(0xC200, 0xC2FF+1), range(0xCF00, 0xEFFF+1))
        #get_oem_range(RID / DID)
    if is_supplier:
        print("Scanning system supplier range 0xf000 - 0xfeff")
        #TODO get_sss_range(RID / DID)
        id_range = it.chain(id_range, range(0xf000, 0xfeff+1))
    if is_safety:
        print("Scanning safety system ranges: \n\t0xfa00 - 0xfa0f"
                "\n\t0xfa19 - 0xfaff")
        #TODO get_sss_range(RID / DID)
        id_range = it.chain(id_range, range(0xf000, 0xfeff+1), range(0xfa19,0xfaff+1))
    if min_id is not None or max_id is not None:
        if min_id > max_id:
            raise ValueError("Can't have MIN > MAX")
        if min_id is None or min_id < 0:
            min_id = 0x0
        if max_id is None or max_id > 0xffff:
            max_id = 0xffff
        print("Scanning custom range 0x{0:02x} - 0x{1:02x}".format(min_id, max_id))
        id_range = it.chain(id_range, range(min_id, max_id+1))
    elif not is_oem and not is_supplier:
        print("Scanning default range 0x{0:02x} - 0x{1:02x}".format(0x0, 0xffff))
        id_range = range(0x0, 0xffff+1)

    return id_range

def scan_routine_control(arb_id_request, arb_id_response, timeout=None, 
        is_oem=False, is_supplier=False, min_id=None, max_id=None, print_results=True):
    routine_map = []
    routine_id_range = []
    #TODO : Add safety ranges for routine control
    if is_oem:
        print("Scanning OEM range 0x0200 - 0xdfff")
        routine_id_range = range(0x0200, 0xdfff+1)
    if is_supplier:
        print("Scanning system supplier range 0xf000 - 0xfeff")
        routine_id_range = it.chain(routine_id_range, range(0xf000, 0xfeff+1))
    if min_id is not None or max_id is not None:
        if min_id > max_id:
            raise ValueError("Can't have MIN > MAX")
        if min_id is None or min_id < 0:
            min_id = 0x0
        if max_id is None or max_id > 0xffff:
            max_id = 0xffff
        print("Scanning custom range 0x{0:02x} - 0x{1:02x}".format(min_id, max_id))
        routine_id_range = it.chain(routine_id_range, range(min_id, max_id+1))
    elif not is_oem and not is_supplier:
        routine_id_range = range(0x0, 0xffff+1)
        

    with IsoTp(arb_id_request=arb_id_request, arb_id_response=arb_id_response) as tp:
        tp.set_filter_single_arbitration_id(arb_id_response)
        with Iso14229_1(tp) as uds:
            if timeout is not None:
                uds.P3_CLIENT = timeout
            try:
                for routine_id in routine_id_range:
                    if print_results:
                        print("\rProbing service 0x{0:02x} routine ID 0x{1:02x} ({1}/{2})".format(
                            ServiceID.ROUTINE_CONTROL, routine_id, 0xffff), end="")
                        stdout.flush()

                    #Purposely use sub_function that is not supported (0x0) to 
                    #trigger error handling. The error 0x12 - SUB_FUNCTION_
                    #NOT_SUPPORTED is unique in the UDS specified error flow
                    #Using it, we can know whether the RID is supported and
                    #whether security is being checked or not. 
                    #To pass min. length check, size must be at least 4,
                    #but some min. length checks may check that optional
                    #data is included, so give 10 bytes optional data to
                    #ensure min-length test is passed.
                    response = uds.routine_control(0x0, routine_id, [1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
                    if response is None:
                        #retry
                        response = uds.routine_control(0x0, routine_id, [1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
                    #Parse response
                    #Positive Bytes: 0x71, sub_func, routine_id1, routine_id2,
                    #               routineInfo, routineStatusRecord1...n
                    #Negative Bytes: 0x7F, service, NRC
                    if Iso14229_1.is_positive_response(response):
                        #shouldn't get here, not supported sub_function
                        routine_map.append([(response[2] << 8) | response[3], "?? Success ?? how"])
                        #TODO: Better error handling
                    else:
                        if response is not None and response[1] == ServiceID.ROUTINE_CONTROL:
                            #if request_out_range, RID not supported in this mode 
                            if response[2] == NegativeResponseCodes.REQUEST_OUT_OF_RANGE:
                                #Because we supply bad sub_function, if REQUEST_OUT_OF_RANGE
                                #returned, then this RID is not supported. Do Nothing.
                                pass
                            elif response[2] == NegativeResponseCodes.SUB_FUNCTION_NOT_SUPPORTED:
                                #Because we supply bad sub_function, if SUB_FUNC_NOT_SUPPORTED
                                #returned, then this RID is supported and passed security check
                                routine_map.append([routine_id, "SUPPORTED_NO_SECURITY"])
                            elif response[2] == NegativeResponseCodes.SECURITY_ACCESS_DENIED:
                                #If security access denied, we know RID is supported
                                routine_map.append([routine_id, "SUPPORTED_SECURITY_ACCESS_DENIED"])
                if print_results:
                    print("\nDone!\n")
            except KeyboardInterrupt:
                if print_results:
                    print("\nInterrupted by user!\n")
    return routine_map
                        

def scan_session_control(arb_id_request, arb_id_response, timeout=None, print_results=True):
    found_sub_funcs = []
    with IsoTp(arb_id_request=arb_id_request, arb_id_response=arb_id_response) as tp:
        # Setup filter for incoming messages
        tp.set_filter_single_arbitration_id(arb_id_response)
        with Iso14229_1(tp) as uds:
            # Set timeout
            if timeout is not None:
                uds.P3_CLIENT = timeout
            try:
                for subfunc_id in range(BaseService.SUB_FUNC_PARAM_MIN, BaseService.SUB_FUNC_PARAM_MAX + 1):
                    if print_results:
                        print("\rProbing service 0x{0:02x} sub-function 0x{1:02x} ({1}/{2}): found {3}".format(
                            ServiceID.DIAGNOSTIC_SESSION_CONTROL, subfunc_id, BaseService.SUB_FUNC_PARAM_MAX, len(found_sub_funcs)), end="")
                        stdout.flush()

                    response = uds.diagnostic_session_control(subfunc_id)
                    if response is None:
                        # No response received
                        #retry strategy
                        time.sleep(1)
                        response = uds.diagnostic_session_control(subfunc_id)
                    # Parse response
                    #Positive Bytes: 0x50, sub_func, data1, data2, data3, data4
                    #Negative Bytes: 0x7F, service, NRC
                    if Iso14229_1.is_positive_response(response):
                        #do positive response thing
                        if response[0] in Services.DiagnosticSessionControl.valid_responses:
                            found_sub_funcs.append(subfunc_id)
                            if subfunc_id == Services.DiagnosticSessionControl.DiagnosticSessionType.PROGRAMMING_SESSION:
                                #Programming Session is special. It can only be exited by reset, default session, or timeout. 
                                #The spec leaves it up to the implementation. This should be made more generic to try reset and
                                #wait for timeout if default session doesn't work..
                                time.sleep(1)
                                uds.diagnostic_session_control(Services.DiagnosticSessionControl.DiagnosticSessionType.DEFAULT_SESSION)
                                #uds.ecu_reset(Services.EcuReset.ResetType.HARD_RESET)
                                time.sleep(1)
                    else:
                        if response is not None and response[1] == ServiceID.DIAGNOSTIC_SESSION_CONTROL:
                            #Only record sub_function if the neg response is for our service
                            if not response[2] == NegativeResponseCodes.SUB_FUNCTION_NOT_SUPPORTED:
                                # Any other response than "service not supported" counts
                                print(response)
                                print("ADDING {} to table".format(subfunc_id))
                                found_sub_funcs.append(subfunc_id)
                if print_results:
                    print("\nDone!\n")
            except KeyboardInterrupt:
                if print_results:
                    print("\nInterrupted by user!\n")
    return found_sub_funcs


def tester_present(arb_id_request, delay, duration, suppress_positive_response):
    """Sends TesterPresent messages to 'arb_id_request'. Stops automatically
    after 'duration' seconds or runs forever if this is None.

    :param arb_id_request: arbitration ID for requests
    :param delay: seconds between each request
    :param duration: seconds before automatically stopping, or None to continue forever
    :param suppress_positive_response: whether positive responses should be suppressed
    :type arb_id_request: int
    :type delay: float
    :type duration: float or None
    :type suppress_positive_response: bool
    """
    # SPR simply tells the recipient not to send a positive response to each TesterPresent message
    if suppress_positive_response:
        sub_function = 0x80
    else:
        sub_function = 0x00

    # Calculate end timestamp if the TesterPresent should automatically stop after a given duration
    auto_stop = duration is not None
    end_time = None
    if auto_stop:
        end_time = datetime.datetime.now() + datetime.timedelta(seconds=duration)

    service_id = Services.TesterPresent.service_id
    message_data = [service_id, sub_function]
    print("Sending TesterPresent to arbitration ID {0} (0x{0:02x})".format(arb_id_request))
    print("\nPress Ctrl+C to stop\n")
    with IsoTp(arb_id_request, None) as can_wrap:
        counter = 1
        while True:
            can_wrap.send_request(message_data)
            print("\rCounter:", counter, end="")
            stdout.flush()
            time.sleep(delay)
            counter += 1
            if auto_stop and datetime.datetime.now() >= end_time:
                break


def __tester_present_wrapper(args):
    """Wrapper used to initiate a TesterPresent session"""
    arb_id_request = args.src
    delay = args.delay
    duration = args.duration
    suppress_positive_response = args.spr

    tester_present(arb_id_request, delay, duration, suppress_positive_response)


def ecu_reset(arb_id_request, arb_id_response, reset_type, timeout):
    """Sends an ECU Reset message to 'arb_id_request'. Returns the first response
    received from 'arb_id_response' within 'timeout' seconds or None otherwise.

    :param arb_id_request: arbitration ID for requests
    :param arb_id_response: arbitration ID for responses
    :param reset_type: value corresponding to a reset type
    :param timeout: seconds to wait for response before timeout, or None for default UDS timeout
    :type arb_id_request: int
    :type arb_id_response int
    :type reset_type: int
    :type timeout: float or None
    :return: list of response byte values on success, None otherwise
    :rtype [int] or None
    """
    # Sanity checks
    if not BYTE_MIN <= reset_type <= BYTE_MAX:
        raise ValueError("reset type must be within interval 0x{0:02x}-0x{1:02x}".format(BYTE_MIN, BYTE_MAX))
    if isinstance(timeout, float) and timeout < 0.0:
        raise ValueError("timeout value ({0}) cannot be negative".format(timeout))

    with IsoTp(arb_id_request=arb_id_request, arb_id_response=arb_id_response) as tp:
        # Setup filter for incoming messages
        tp.set_filter_single_arbitration_id(arb_id_response)
        with Iso14229_1(tp) as uds:
            # Set timeout
            if timeout is not None:
                uds.P3_CLIENT = timeout

            response = uds.ecu_reset(reset_type=reset_type)
            return response


def __ecu_reset_wrapper(args):
    """Wrapper used to initiate ECU Reset"""
    arb_id_request = args.src
    arb_id_response = args.dst
    reset_type = args.reset_type
    timeout = args.timeout

    print("Sending ECU reset, type 0x{0:02x} to arbitration ID {1} (0x{1:02x})".format(reset_type, arb_id_request))
    try:
        response = ecu_reset(arb_id_request, arb_id_response, reset_type, timeout)
    except ValueError as e:
        print("ValueError: {0}".format(e))
        return

    # Decode response
    decode_response(response, Services.EcuReset.service_id, reset_type)

#Return 0 on positive or negative response, 1 on failure
def decode_response(response, expected_response_id, expected_subfunc):
    if response is None:
        print("No response was received")
        return 1
    else:
        response_length = len(response)
        if response_length == 0:
            # Empty response
            print("Received empty response")
            return 1
        elif response_length == 1:
            # Invalid response length
            print("Received response [{0:02x}] (1 byte), expected at least 2 bytes".format(response[0], len(response)))
            return 1
        elif Iso14229_1.is_positive_response(response):
            # Positive response handling
            response_service_id = response[0]
            subfunction = response[1]
            expected_response_id = Iso14229_1.get_service_response_id(expected_response_id)
            if response_service_id == expected_response_id and subfunction == expected_subfunc:
                # Positive response
                pos_msg = "Received positive response"
                if response_length > 2:
                    # Additional data can be seconds left to reset (powerDownTime) or manufacturer specific
                    additional_data = list_to_hex_str(response[2:], ",")
                    pos_msg += " with additional data: [{0}]".format(
                                                            additional_data)
                print(pos_msg)
            else:
                # Service and/or subfunction mismatch
                print("Response service ID 0x{0:02x} and subfunction "
                    "0x{1:02x} do not match expected values 0x{2:02x} "
                    "and 0x{3:02x}".format(response_service_id,
                    subfunction, Services.EcuReset.service_id, reset_type))
        else:
            # Negative response handling
            print_negative_response(response)

def print_negative_response(response):
    """
    Helper function for decoding and printing a negative response received
    from a UDS server.

    :param response: Response data after CAN-TP layer has been removed
    :type response: [int]

    :return: Nothing
    """
    nrc = response[2]
    nrc_description = NRC_NAMES.get(nrc, "Unknown NRC value")
    print("Received negative response code (NRC) 0x{0:02x}: {1}"
                .format(nrc, nrc_description))

def __security_seed_wrapper(args):
    """Wrapper used to initiate secuirty seed dump"""
    arb_id_request = args.src
    arb_id_response = args.dst
    reset_type = args.reset
    session_type = args.sess_type
    level = args.sec_level
    num_seeds = args.num

    seed_list = []
    try:
        print("Security Seed dump started. To end, use Ctrl+C and a report "
                "will be output to stdout.\n")
        while num_seeds > len(seed_list) or num_seeds == 0:
            #Extended diagnostics
            response = extended_session(arb_id_request, arb_id_response,
                                                                session_type)
            if response is None:
                #simple retry in-case bus wasn't awake for first request
                response = extended_session(arb_id_request, arb_id_response,
                                                                session_type)
            #Request seed
            response = request_seed(arb_id_request, arb_id_response,
                            level, None, None)
            if Iso14229_1.is_positive_response(response):
                seed_list.append(list_to_hex_str(response[2:]))
                print("Seed received: {}\t(Total captured: {})"
			.format(list_to_hex_str(response[2:]),
			len(seed_list)), end="\r")
                stdout.flush()
            else:
                print_negative_response(response)
                break
            if reset_type:
                ecu_reset(arb_id_request, arb_id_response, reset_type, None)
                if reset_type == Services.EcuReset.ResetType.HARD_RESET:
                    time.sleep(0.5)
    except KeyboardInterrupt:
        print("Interrupted by user.")
    except ValueError as e:
        print(e)
        print("For help, use the '-h' flag")
        return

    if len(seed_list) > 0:
        print("\n")
        print("Security Access Seeds Captured:")
        for seed in seed_list:
            print(seed)

def extended_session(arb_id_request, arb_id_response):
    return diag_session_control(arb_id_request, arb_id_response, 
        Services.DiagnosticSessionControl.DiagnosticSessionType.EXTENDED_DIAGNOSTIC_SESSION)

def diag_session_control(arb_id_request, arb_id_response, session_type):
    # Sanity checks
    if not Services.DiagnosticSessionControl.DiagnosticSessionType().is_valid_session(session_type):
        raise ValueError("Invalid extended session type: 0x{0:02x}".format(session_type))
    with IsoTp(arb_id_request=arb_id_request, arb_id_response=arb_id_response) as tp:
        # Setup filter for incoming messages
        tp.set_filter_single_arbitration_id(arb_id_response)
        with Iso14229_1(tp) as uds:
            response = uds.diagnostic_session_control(session_type)
            return response

def request_seed(arb_id_request, arb_id_response, level, data_record, timeout):
    """Sends an Request seed message to 'arb_id_request'. Returns the first response
    received from 'arb_id_response' within 'timeout' seconds or None otherwise.

    :param arb_id_request: arbitration ID for requests
    :param arb_id_response: arbitration ID for responses
    :param level: vehicle manufacturer specific access level to request seed for
    :param data_record: optional vehicle manufacturer specific data to transmit when requesting seed
    :param timeout: seconds to wait for response before timeout, or None for default UDS timeout
    :type arb_id_request: int
    :type arb_id_response: int
    :type level: int
    :type data_record: [int] or None
    :type timeout: float or None
    :return: list of response byte values on success, None otherwise
    :rtype [int] or None
    """
    # Sanity checks
    if not Services.SecurityAccess.RequestSeedOrSendKey().is_valid_request_seed_level(level):
        raise ValueError("Invalid request seed level")
    if isinstance(timeout, float) and timeout < 0.0:
        raise ValueError("timeout value ({0}) cannot be negative".format(timeout))

    with IsoTp(arb_id_request=arb_id_request, arb_id_response=arb_id_response) as tp:
        # Setup filter for incoming messages
        tp.set_filter_single_arbitration_id(arb_id_response)
        with Iso14229_1(tp) as uds:
            # Set timeout
            if timeout is not None:
                uds.P3_CLIENT = timeout

            response = uds.security_access_request_seed(level, data_record)
            return response


def send_key(arb_id_request, arb_id_response, level, key, timeout):
    """
    Sends an Send key message to 'arb_id_request'. Returns the first response
    received from 'arb_id_response' within 'timeout' seconds or None otherwise.

    :param arb_id_request: arbitration ID for requests
    :param arb_id_response: arbitration ID for responses
    :param level: vehicle manufacturer specific access level to send key for
    :param key: key to transmit
    :param timeout: seconds to wait for response before timeout, or None for default UDS timeout
    :type arb_id_request: int
    :type arb_id_response: int
    :type level: int
    :type key: [int]
    :type timeout: float or None
    :return: list of response byte values on success, None otherwise
    :rtype [int] or None
    """
    # Sanity checks
    if not Services.SecurityAccess.RequestSeedOrSendKey().is_valid_send_key_level(level):
        raise ValueError("Invalid send key level")
    if isinstance(timeout, float) and timeout < 0.0:
        raise ValueError("timeout value ({0}) cannot be negative".format(timeout))

    with IsoTp(arb_id_request=arb_id_request, arb_id_response=arb_id_response) as tp:
        # Setup filter for incoming messages
        tp.set_filter_single_arbitration_id(arb_id_response)
        with Iso14229_1(tp) as uds:
            # Set timeout
            if timeout is not None:
                uds.P3_CLIENT = timeout

            response = uds.security_access_send_key(level=level, key=key)
            return response


def __parse_args(args):
    """Parser for module arguments"""
    parser = argparse.ArgumentParser(prog="cc.py uds",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="""Universal Diagnostic Services module for CaringCaribou""",
                                     epilog="""Example usage:
  cc.py uds discovery
  cc.py uds discovery --blacklist 0x123 0x456
  cc.py uds discovery --autoblacklist 10
  cc.py uds services 0x733 0x633
  cc.py uds service_scan 0x10 0x733 0x633
  cc.py uds ecu_reset 1 0x733 0x633
  cc.py uds testerpresent 0x733
  cc.py uds security_seed 0x3 0x1 0x733 0x633 -r 1""")
    subparsers = parser.add_subparsers(dest="module_function")
    subparsers.required = True

    # Parser for diagnostics discovery
    parser_discovery = subparsers.add_parser("discovery")
    parser_discovery.add_argument("-min", type=parse_int_dec_or_hex, default=None,
                                  help="min arbitration ID to send request for")
    parser_discovery.add_argument("-max", type=parse_int_dec_or_hex, default=None,
                                  help="max arbitration ID to send request for")
    parser_discovery.add_argument("-b", "--blacklist", metavar="B", type=parse_int_dec_or_hex, default=[], nargs="+",
                                  help="arbitration IDs to blacklist responses from")
    parser_discovery.add_argument("-ab", "--autoblacklist", metavar="N", type=float, default=0,
                                  help="listen for false positives for N seconds and blacklist matching "
                                       "arbitration IDs before running discovery")
    parser_discovery.add_argument("-sv", "--skipverify", action="store_true",
                                  help="skip verification step (reduces result accuracy)")
    parser_discovery.add_argument("-d", "--delay", metavar="D", type=float, default=DELAY_DISCOVERY,
                                  help="D seconds delay between messages (default: {0})".format(DELAY_DISCOVERY))
    parser_discovery.set_defaults(func=__uds_discovery_wrapper)

    # Parser for diagnostics service discovery
    parser_info = subparsers.add_parser("services")
    parser_info.add_argument("src", type=parse_int_dec_or_hex, help="arbitration ID to transmit to")
    parser_info.add_argument("dst", type=parse_int_dec_or_hex, help="arbitration ID to listen to")
    parser_info.add_argument("-t", "--timeout", metavar="T", type=float, default=TIMEOUT_SERVICES,
                             help="wait T seconds for response before timeout (default: {0})".format(TIMEOUT_SERVICES))
    parser_info.set_defaults(func=__service_discovery_wrapper)

    # Parser for diagnostics service scan
    parser_servscan = subparsers.add_parser("service_scan")
    parser_servscan.add_argument("service", type=parse_int_dec_or_hex, 
        help="supported service to scan: 0x31")
    parser_servscan.add_argument("src", type=parse_int_dec_or_hex, 
        help="arbitration ID to transmit to")
    parser_servscan.add_argument("dst", type=parse_int_dec_or_hex, 
        help="arbitration ID to listen to")
    parser_servscan.add_argument("-t", "--timeout", metavar="T", 
        type=float, default=TIMEOUT_SERVICES,
        help="wait T seconds for response before timeout (default: "
        "{0})".format(TIMEOUT_SERVICES))
    parser_servscan.add_argument("-oem", action="store_true", 
        help="Scan vehicle manufacturer specific ranges for applicable services")
    parser_servscan.add_argument("-sss", action="store_true", 
        help="Scan system supplier specific ranges for applicable services")
    parser_servscan.add_argument("-saf", action="store_true",
        help="Scan safety system specific ranges for applicable services") 
    parser_servscan.add_argument("-min", type=parse_int_dec_or_hex, default=None,
        help="min value to start scanning with")
    parser_servscan.add_argument("-max", type=parse_int_dec_or_hex, default=None,
        help="max value to start scanning with")
    parser_servscan.set_defaults(func=__service_scan_wrapper)

    # Parser for diagnostics service scan
    parser_extservscan = subparsers.add_parser("ext_service_scan")
    parser_extservscan.add_argument("service", type=parse_int_dec_or_hex, 
        help="supported service to scan: 0x31")
    parser_extservscan.add_argument("src", type=parse_int_dec_or_hex, 
        help="arbitration ID to transmit to")
    parser_extservscan.add_argument("dst", type=parse_int_dec_or_hex, 
        help="arbitration ID to listen to")
    parser_extservscan.add_argument("-t", "--timeout", metavar="T", 
        type=float, default=TIMEOUT_SERVICES,
        help="wait T seconds for response before timeout (default: "
                "{0})".format(TIMEOUT_SERVICES))
    parser_extservscan.add_argument("-oem", action="store_true", 
        help="Scan vehicle manufacturer specific ranges for applicable services")
    parser_extservscan.add_argument("-sss", action="store_true", 
        help="Scan system supplier specific ranges for applicable services")
    parser_extservscan.add_argument("-saf", action="store_true",
        help="Scan safety system specific ranges for applicable services") 
    parser_extservscan.add_argument("-min", type=parse_int_dec_or_hex, default=None,
        help="min value to start scanning with")
    parser_extservscan.add_argument("-max", type=parse_int_dec_or_hex, default=None,
        help="max value to start scanning with")
    parser_extservscan.set_defaults(func=__ext_service_scan_wrapper)


    # Parser for ECU Reset
    parser_ecu_reset = subparsers.add_parser("ecu_reset")
    parser_ecu_reset.add_argument("reset_type", metavar="type", type=parse_int_dec_or_hex,
                                  help="Reset type: 1=hard, 2=key off/on, 3=soft, "
                                    "4=enable rapid power shutdown, 5=disable rapid power shutdown")
    parser_ecu_reset.add_argument("src", type=parse_int_dec_or_hex, help="arbitration ID to transmit to")
    parser_ecu_reset.add_argument("dst", type=parse_int_dec_or_hex, help="arbitration ID to listen to")
    parser_ecu_reset.add_argument("-t", "--timeout", type=float, metavar="T",
                                  help="wait T seconds for response before timeout")
    parser_ecu_reset.set_defaults(func=__ecu_reset_wrapper)

    # Parser for TesterPresent
    parser_tp = subparsers.add_parser("testerpresent")
    parser_tp.add_argument("src", type=parse_int_dec_or_hex, help="arbitration ID to transmit to")
    parser_tp.add_argument("-d", "--delay", metavar="D", type=float, default=DELAY_TESTER_PRESENT,
                           help="send TesterPresent every D seconds (default: {0})".format(DELAY_TESTER_PRESENT))
    parser_tp.add_argument("-dur", "--duration", metavar="S", type=float, help="automatically stop after S seconds")
    parser_tp.add_argument("-spr", action="store_true", help="suppress positive response")
    parser_tp.set_defaults(func=__tester_present_wrapper)


    # Parser for SecuritySeedDump
    parser_secseed = subparsers.add_parser("security_seed")
    parser_secseed.add_argument("sess_type", metavar="stype",
            type=parse_int_dec_or_hex, help="Session Type: 1=defaultSession "
            "2=programmingSession 3=extendedSession 4=safetySession [0x40"
            "-0x5F]=OEM [0x60-0x7E]=Supplier [0x0, 0x5-0x3F, 0x7F]=ISOSAE"
            "Reserved")
    parser_secseed.add_argument("sec_level", metavar="level",
            type=parse_int_dec_or_hex, help="Security level: [0x1 - 0x41"
            " (odd only)]=OEM 0x5F=EOLPyrotechnics [0x61-0x7E]=Supplier "
            "[0x0, 0x43-0x5E, 0x7F]=ISOSAEReserved")
    parser_secseed.add_argument("src", type=parse_int_dec_or_hex,
            help="arbitration ID to transmit to")
    parser_secseed.add_argument("dst", type=parse_int_dec_or_hex,
            help="arbitration ID to listen to")
    parser_secseed.add_argument("-r", "--reset", metavar="rtype",
            type=parse_int_dec_or_hex, help="Enable reset between security "
            "seed requests. Reset type: 1=hardReset, 2=key off/on, "
            "3=softReset, 4=enable rapid power shutdown, 5=disable rapid "
            "power shutdown")
    parser_secseed.add_argument("-n", "--num", metavar="NUM",
            type=parse_int_dec_or_hex, help="Specify a positive number of " 
            "security seeds to capture before terminating. A '0' is "
            "interpreted as infinity. (default: 0)")
    parser_secseed.set_defaults(func=__security_seed_wrapper)



    args = parser.parse_args(args)
    return args


def module_main(arg_list):
    """Module main wrapper"""
    try:
        args = __parse_args(arg_list)
        args.func(args)
    except KeyboardInterrupt:
        print("\n\nTerminated by user")
