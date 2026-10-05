#![allow(non_snake_case, non_camel_case_types, non_upper_case_globals, dead_code)]

// The dependency-free raw Win32 implementation is assembled by build.rs from source parts.
include!(concat!(env!("OUT_DIR"), "/windows_app_generated.rs"));
