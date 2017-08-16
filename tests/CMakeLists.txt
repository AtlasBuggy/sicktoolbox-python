cmake_minimum_required(VERSION 2.8.3)

set(PYTHON_LIBRARY /usr/local/Cellar/python3/3.6.2/Frameworks/Python.framework/Versions/3.6/lib/libpython3.6.dylib)
set(PYTHON_INCLUDE_DIR /usr/local/Cellar/python3/3.6.2/Frameworks/Python.framework/Versions/3.6/include/python3.6m/)
set(PYTHON_EXECUTABLE /usr/local/bin/python3)

FIND_PACKAGE(PythonInterp 3.6 REQUIRED)
FIND_PACKAGE(PythonLibs 3.6 REQUIRED)

# include(FindPythonLibs)

# INCLUDE_DIRECTORIES(${PYTHON_LIBRARIES})
# INCLUDE_DIRECTORIES(${PYTHON_INCLUDE_DIRS})

# FIND_PACKAGE(PythonInterp)
# FIND_PACKAGE(PythonLibs)

FIND_PACKAGE(Boost COMPONENTS python3 REQUIRED)
IF (Boost_FOUND)
    INCLUDE_DIRECTORIES(${Boost_INCLUDE_DIR})
    ADD_DEFINITIONS( "-DHAS_BOOST" )
ENDIF()

ENABLE_TESTING()
INCLUDE_DIRECTORIES(${Boost_INCLUDE_DIRS} ${PYTHON_INCLUDE_DIRS})
LINK_LIBRARIES(${Boost_LIBRARIES} ${PYTHON_LIBRARIES})

PYTHON_ADD_MODULE(sicktoolbox sicktoolbox.cpp)
FILE(COPY sicktoolbox.py DESTINATION .)
# ADD_TEST(NAME 01-HelloWorld COMMAND ${PYTHON_EXECUTABLE} hello.py)

INCLUDE_DIRECTORIES(/usr/local/include/sicklms-1.0)
# LINK_DIRECTORIES(/usr/local/lib/libsicklms-1.0.0.0.0.dylib)
target_link_libraries(sicktoolbox sicklms-1.0)

# add_library(sicklms-1.0 STATIC IMPORTED)
#
# set_property(TARGET sicklms-1.0 PROPERTY IMPORTED_LOCATION /Users/Woz4tetra/Documents/Code/LMS200/sicktoolbox-1.0.1/c++/drivers/lms/sicklms-1.0/libsicklms-1.0.la)
#
# add_dependencies(sicktoolbox sicklms-1.0)
#
#
# INCLUDE_DIRECTORIES(/Users/Woz4tetra/Documents/Code/LMS200/sicktoolbox-1.0.1/c++/drivers/lms/sicklms-1.0)
# LINK_DIRECTORIES(/Users/Woz4tetra/Documents/Code/LMS200/sicktoolbox-1.0.1/c++/drivers/lms/sicklms-1.0/.libs)
# # add_executable(SickLMS SickLMS.cc)
# target_link_libraries(sicktoolbox sicklms-1.0)
#
# INCLUDE_DIRECTORIES(/Users/Woz4tetra/Documents/Code/LMS200/sicktoolbox-1.0.1/c++/drivers/base/src/)
# # target_link_libraries(sicktoolbox sicklms-1.0)
