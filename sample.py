import r2py

r2py.configs.log_file = "/tmp/r2py.logs"; # Same as default log file

r2py.r2py("sample_input_file_path.R", "sample_output_file_path.py");

print "\n\nsample_output_file_path.py file must have been created...\n\n";

if(False):
	r2py.r2py_recursive("input_folder_path/", "output_folder_path/");
print """\n\n r2py_recursive would have created 'output_folder_path' folder, having same directry tree structure as 'input_folder_path' but convered py files in place of R files \n\n\n""";

