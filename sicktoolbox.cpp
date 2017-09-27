#include <boost/python.hpp>
#include <SickLMS.hh>
using namespace boost::python;
using namespace SickToolbox;

unsigned int values[SickLMS::SICK_MAX_NUM_MEASUREMENTS] = {0};
unsigned int num_values = 0;

tuple GetScan(SickLMS *sick_lms) {
    sick_lms->GetSickScan(values, num_values);

    list values_list;
    for (int index = 0; index < num_values; index++) {
        values_list.append(values[index]);
    }
    return tuple(values_list);
}

//PyObject *sickIOExceptionType = NULL;
//
//void translateSickIOException(SickIOException const &e)
//{
//    assert(sickIOExceptionType != NULL);
//    object pythonExceptionInstance(e);
//    PyErr_SetObject(sickIOExceptionType, pythonExceptionInstance.ptr());
//}

BOOST_PYTHON_MODULE(sicktoolbox)
{
    class_<SickLMS>("SickLMS", init<std::string>())
        .def("initialize", &SickLMS::Initialize)
        .def("get_scan", GetScan)
        .def("uninitialize", &SickLMS::Uninitialize)

        .def("get_operating_mode", &SickToolbox::SickLMS::GetSickOperatingMode)
        .def("get_measuring_mode", &SickToolbox::SickLMS::GetSickMeasuringMode)
        .def("get_measuring_units", &SickToolbox::SickLMS::GetSickMeasuringUnits)
        .def("get_scan_resolution", &SickToolbox::SickLMS::GetSickScanResolution)
        .def("get_scan_angle", &SickToolbox::SickLMS::GetSickScanAngle)
    ;
    enum_<SickLMS::sick_lms_baud_t>("bauds")
        .value("SICK_BAUD_9600", SickToolbox::SickLMS::SICK_BAUD_9600)
        .value("SICK_BAUD_19200", SickToolbox::SickLMS::SICK_BAUD_19200)
        .value("SICK_BAUD_38400", SickToolbox::SickLMS::SICK_BAUD_38400)
        .value("SICK_BAUD_500K", SickToolbox::SickLMS::SICK_BAUD_500K)
        .value("SICK_BAUD_UNKNOWN", SickToolbox::SickLMS::SICK_BAUD_UNKNOWN)
    ;

    enum_<SickLMS::sick_lms_measuring_units_t>("units")
        .value("CM", SickToolbox::SickLMS::SICK_MEASURING_UNITS_CM)
        .value("MM", SickToolbox::SickLMS::SICK_MEASURING_UNITS_MM)
        .value("UNKNOWN", SickToolbox::SickLMS::SICK_MEASURING_UNITS_UNKNOWN)
    ;

    enum_<SickLMS::sick_lms_operating_mode_t>("operating_modes")
        .value("INSTALLATION", SickToolbox::SickLMS::SICK_OP_MODE_INSTALLATION)
        .value("DIAGNOSTIC", SickToolbox::SickLMS::SICK_OP_MODE_DIAGNOSTIC)
        .value("MONITOR_STREAM_MIN_VALUE_FOR_EACH_SEGMENT", SickToolbox::SickLMS::SICK_OP_MODE_MONITOR_STREAM_MIN_VALUE_FOR_EACH_SEGMENT)
        .value("MONITOR_TRIGGER_MIN_VALUE_ON_OBJECT", SickToolbox::SickLMS::SICK_OP_MODE_MONITOR_TRIGGER_MIN_VALUE_ON_OBJECT)
        .value("MONITOR_STREAM_MIN_VERT_DIST_TO_OBJECT", SickToolbox::SickLMS::SICK_OP_MODE_MONITOR_STREAM_MIN_VERT_DIST_TO_OBJECT)
        .value("MONITOR_TRIGGER_MIN_VERT_DIST_TO_OBJECT", SickToolbox::SickLMS::SICK_OP_MODE_MONITOR_TRIGGER_MIN_VERT_DIST_TO_OBJECT)
        .value("MONITOR_STREAM_VALUES", SickToolbox::SickLMS::SICK_OP_MODE_MONITOR_STREAM_VALUES)
        .value("MONITOR_REQUEST_VALUES", SickToolbox::SickLMS::SICK_OP_MODE_MONITOR_REQUEST_VALUES)
        .value("MONITOR_STREAM_MEAN_VALUES", SickToolbox::SickLMS::SICK_OP_MODE_MONITOR_STREAM_MEAN_VALUES)
        .value("MONITOR_STREAM_VALUES_SUBRANGE", SickToolbox::SickLMS::SICK_OP_MODE_MONITOR_STREAM_VALUES_SUBRANGE)
        .value("MONITOR_STREAM_MEAN_VALUES_SUBRANGE", SickToolbox::SickLMS::SICK_OP_MODE_MONITOR_STREAM_MEAN_VALUES_SUBRANGE)
        .value("MONITOR_STREAM_VALUES_WITH_FIELDS", SickToolbox::SickLMS::SICK_OP_MODE_MONITOR_STREAM_VALUES_WITH_FIELDS)
        .value("MONITOR_STREAM_VALUES_FROM_PARTIAL_SCAN", SickToolbox::SickLMS::SICK_OP_MODE_MONITOR_STREAM_VALUES_FROM_PARTIAL_SCAN)
        .value("MONITOR_STREAM_RANGE_AND_REFLECT_FROM_PARTIAL_SCAN", SickToolbox::SickLMS::SICK_OP_MODE_MONITOR_STREAM_RANGE_AND_REFLECT_FROM_PARTIAL_SCAN)
        .value("MONITOR_STREAM_MIN_VALUES_FOR_EACH_SEGMENT_SUBRANGE", SickToolbox::SickLMS::SICK_OP_MODE_MONITOR_STREAM_MIN_VALUES_FOR_EACH_SEGMENT_SUBRANGE)
        .value("MONITOR_NAVIGATION", SickToolbox::SickLMS::SICK_OP_MODE_MONITOR_NAVIGATION)
        .value("MONITOR_STREAM_RANGE_AND_REFLECT", SickToolbox::SickLMS::SICK_OP_MODE_MONITOR_STREAM_RANGE_AND_REFLECT)
        .value("UNKNOWN", SickToolbox::SickLMS::SICK_OP_MODE_UNKNOWN)
    ;

    enum_<SickLMS::sick_lms_measuring_mode_t>("measuring_modes")
        .value("MODE_8_OR_80_FA_FB_DAZZLE", SickToolbox::SickLMS::SICK_MS_MODE_8_OR_80_FA_FB_DAZZLE)
        .value("MODE_8_OR_80_REFLECTOR", SickToolbox::SickLMS::SICK_MS_MODE_8_OR_80_REFLECTOR)
        .value("MODE_8_OR_80_FA_FB_FC", SickToolbox::SickLMS::SICK_MS_MODE_8_OR_80_FA_FB_FC)
        .value("MODE_16_REFLECTOR", SickToolbox::SickLMS::SICK_MS_MODE_16_REFLECTOR)
        .value("MODE_16_FA_FB", SickToolbox::SickLMS::SICK_MS_MODE_16_FA_FB)
        .value("MODE_32_REFLECTOR", SickToolbox::SickLMS::SICK_MS_MODE_32_REFLECTOR)
        .value("MODE_32_FA", SickToolbox::SickLMS::SICK_MS_MODE_32_FA)
        .value("MODE_32_IMMEDIATE", SickToolbox::SickLMS::SICK_MS_MODE_32_IMMEDIATE)
        .value("MODE_REFLECTIVITY", SickToolbox::SickLMS::SICK_MS_MODE_REFLECTIVITY)
        .value("MODE_UNKNOWN", SickToolbox::SickLMS::SICK_MS_MODE_UNKNOWN)
    ;

    class_<SickLMS::sick_lms_operating_status_t>("operation")
        .add_property("scan_angle", &SickLMS::sick_lms_operating_status_t::sick_scan_angle)
        .add_property("scan_resolution", &SickLMS::sick_lms_operating_status_t::sick_scan_resolution)
        .add_property("num_motor_revs", &SickLMS::sick_lms_operating_status_t::sick_num_motor_revs)
        .add_property("operating_mode", &SickLMS::sick_lms_operating_status_t::sick_operating_mode)
        .add_property("measuring_mode", &SickLMS::sick_lms_operating_status_t::sick_measuring_mode)
        .add_property("laser_mode", &SickLMS::sick_lms_operating_status_t::sick_laser_mode)
        .add_property("device_status", &SickLMS::sick_lms_operating_status_t::sick_device_status)
        .add_property("measuring_units", &SickLMS::sick_lms_operating_status_t::sick_measuring_units)
        .add_property("address", &SickLMS::sick_lms_operating_status_t::sick_address)
        .add_property("variant", &SickLMS::sick_lms_operating_status_t::sick_variant)
    ;

//    class_<SickIOException>SickIOExceptionClass("SickIOException");
//    sickIOExceptionType = SickIOExceptionClass.ptr();
//    register_exception_translator<SickIOException>(&translateSickIOException);

    class_<SickIOException>("SickIOException");
    class_<SickTimeoutException>("SickTimeoutException");
    class_<SickConfigException>("SickConfigException");
}
