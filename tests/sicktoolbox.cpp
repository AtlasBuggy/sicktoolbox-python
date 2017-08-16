#include <boost/python.hpp>
#include <SickLMS.hh>
using namespace boost::python;
using namespace SickToolbox;

unsigned int values[SickLMS::SICK_MAX_NUM_MEASUREMENTS] = {0};
unsigned int num_values = 0;

boost::python::tuple GetScan(SickLMS *sick_lms) {
    sick_lms->GetSickScan(values, num_values);

    list values_list;
    for (int index = 0; index < num_values; index++) {
        values_list.append(values[index]);
    }
    return tuple(values_list);
}

BOOST_PYTHON_MODULE(sicktoolbox)
{
    class_<SickLMS>("SickLMS", init<std::string>())
        .def("initialize", &SickLMS::Initialize)
        .def("get_scan", GetScan)
        .def("uninitialize", &SickLMS::Uninitialize)
    ;
    enum_<SickLMS::sick_lms_baud_t>("Bauds")
        .value("SICK_BAUD_9600", SickToolbox::SickLMS::SICK_BAUD_9600)
        .value("SICK_BAUD_19200", SickToolbox::SickLMS::SICK_BAUD_19200)
        .value("SICK_BAUD_38400", SickToolbox::SickLMS::SICK_BAUD_38400);

    class_<SickIOException>("SickIOException");
    class_<SickTimeoutException>("SickTimeoutException");
    class_<SickConfigException>("SickConfigException");
}
