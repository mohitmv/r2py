
from msl import *


import json, os, numpy, time, pytz


status_messages = {
	1: "Converted Successfully", 
	-1: "Failed to parse R code", 

};

configs = Object(log_file="/tmp/r2py.logs");

Time.__init__(pytz);
log = lambda data: Help.write_log(configs.log_file, "r2py", data);


compare = lambda x, y, key='1': (x['col'+key].__cmp__(y['col'+key]) if (x['line'+key]==y['line'+key]) else x['line'+key].__cmp__(y['line'+key]));

is_x_inside_y = lambda x,y: (compare(x, y, '1')>=0 and compare(x,y,'2')<=0 and (compare(x,y,"1")==1 or compare(x,y,"2")==-1));

def input_and_init(input_file):
	global nodes, edges, parsed_code, indexed_parsed_code, state;

	# input_file = "student.r";

	randomstr = str(int(time.time()));

	tmp_r_file = "/tmp/tmp_"+randomstr+".r";
	parsed_code_file = "/tmp/parsed_code_"+randomstr+".json";

	r_code = """

	input_file = \""""+input_file+"""\";

	input_content <- "
	"""+ ("".join(map(lambda x: {'\"': '\\\"', '\\': '\\\\'}.get(x, x), read_file(input_file)))) + """
	"
	sf <- srcfile(input_file);
	try(parse(text = input_content, srcfile = sf))
	p = getParseData(sf);
	library(jsonlite)
	x <- toJSON(p)
	output_file = file(\""""+ parsed_code_file +"""\");
	writeLines(x, output_file);
	close(output_file);
	""";

	write_file(tmp_r_file, r_code);
	run_linux_command("r -f "+tmp_r_file+" 2>/tmp/warnings ");
	os.remove(tmp_r_file);
	# print tmp_r_file;
	parsed_code = json.loads(read_file(parsed_code_file));
	os.remove(parsed_code_file);
	nodes = {};
	edges = {};
	parsed_code = list(i for i in parsed_code if i['token'] != "COMMENT");
	indexed_parsed_code = indexify(parsed_code, ['id'], is_unique=True, is_pop=False);

	state = Object(
		lambda_function_id=0, 
		global_functions = [], 
	);


def create_graph():
	for i in parsed_code:
		node_id = "{0}.{1}-{2}.{3}".format(i['line1'], i['col1'], i['line2'], i['col2']);
		i['node_id'] = node_id;
		soft_set(nodes, node_id, {"tokens":[], "out_going": set(), "in_coming": set(), "rank": -1, "node_id": node_id});
		nodes[node_id]["tokens"].append(i);

	def divide_and_conquer(inp): #Will return in n*log(n) time surely.
		if(len(inp) <= 5):
			return atomic_list(inp);
		min_line = 1000000000000;
		max_line = -1;
		for i in inp:
			min_line = min(min_line, nodes[i]['tokens'][0]['line1']);
			max_line = max(max_line, nodes[i]['tokens'][0]['line2']);

		upper_part = [];
		middle_part = [];
		bottom_part = [];
		middle = (min_line+max_line)/2;
		min_middle_top = 1000000000000;
		max_middle_bottom = -1;
		for i in inp:
			if(nodes[i]['tokens'][0]['line2'] <= middle):
				upper_part.append(i);
			elif(nodes[i]['tokens'][0]['line1'] > middle):
				bottom_part.append(i);
			else:
				middle_part.append(i);
				min_middle_top = min(min_middle_top, nodes[i]['tokens'][0]['line1']);
				max_middle_bottom = max(max_middle_bottom, nodes[i]['tokens'][0]['line2']);

		if(max(len(upper_part), len(middle_part), len(bottom_part)) == len(inp)):
			return atomic_list(inp);

		target_part = [];
		for i in upper_part:
			if(nodes[i]['tokens'][0]['line1'] >= min_middle_top):
				target_part.append(i);

		for i in bottom_part:
			if(nodes[i]['tokens'][0]['line2'] <= max_middle_bottom):
				target_part.append(i);

		for i in middle_part:
			for j in target_part:
				if(i!=j and is_x_inside_y(nodes[j]['tokens'][0], nodes[i]['tokens'][0])):
					nodes[j]['out_going'].add(i);
					nodes[i]['in_coming'].add(j);

		divide_and_conquer(upper_part);
		divide_and_conquer(middle_part);
		divide_and_conquer(bottom_part);



	def atomic_list(inp):
		for i in inp:
			ii = nodes[i]['tokens'][0];
			for j in inp:
				jj = nodes[j]['tokens'][0];
				if(i!=j and is_x_inside_y(jj, ii)):
					nodes[j]['out_going'].add(i);
					nodes[i]['in_coming'].add(j);

	divide_and_conquer(nodes.keys());


def topological_sorting(): # "topological sorting in DAG"
	for ii in nodes:
		i = nodes[ii];
		i['tmp_in_coming'] = set(i['in_coming']);
		i['tmp_out_going'] = set(i['out_going']);

	L = [];
	S = list(i for i in nodes if len(nodes[i]['tmp_in_coming'])==0);
	while(len(S)>0):
		n=S.pop();
		L.append(n);
		for m in nodes[n]['tmp_out_going']:
			nodes[m]['tmp_in_coming'].remove(n);
			if(len(nodes[m]['tmp_in_coming']) == 0):
				S.append(m);
		nodes[n]['tmp_out_going'] = set();
	for i in xrange(len(L)):
		nodes[L[i]]['rank'] = i;


def get_all_tokens():
	return set(i["token"] for i in parsed_code);


def create_parent_relation():
	for i in nodes:
		tokens = nodes[i]['tokens'];
		indexed_tokens = indexify(tokens, ['token'], is_pop=False, is_unique=True);
		nodes[i]['tokens'] = partial_dict(indexed_tokens, ["expr"]+indexed_tokens.keys()).values();

	for i in nodes:
		tokens = nodes[i]['tokens'];
		for jj in xrange(len(tokens)):
			j = tokens[jj];
			j['children'] = [];
			if(len(nodes[j['node_id']]['out_going']) == 0):
				j['parent'] = 0;
			elif(jj > 0):
				j['parent'] = tokens[0]['id'];
			else:
				j['parent'] = nodes[min(nodes[j['node_id']]['out_going'], key=lambda x: nodes[x]['rank'])]['tokens'][-1]['id'];


	super_node = {'parent': None, "id": 0, "children": [], 'token': "exprlist", "text": ""};
	indexed_parsed_code[0] = super_node;
	parsed_code.append(super_node);

	for i in parsed_code:
		if(i['id'] != 0):
			indexed_parsed_code[i['parent']]['children'].append(i['id']);

	for i in parsed_code:
		i['children'] = sorted(i['children'], lambda x,y: compare( indexed_parsed_code[x], indexed_parsed_code[y],'1'));



def clean_tree1(subtree):
	helper = lambda subtree: {"text": subtree["text"], "token": subtree["token"], "children": list(helper(indexed_parsed_code[x]) for x in subtree['children'])};
	return helper(subtree);


must_transform = soft_merge({}, dict((i, "v_"+i) for i in ["str", "list", "with", "and", "assert", "break", "class", "continue", "def"	, "del", "elif", "except", "exec", "finally", "from", "global", "import", "is", "lambda", "not", "or", "pass", "raise", "try"] + ["Data", "Float", "Int", "Numeric", "Oxphys", "array", "close", "float", "int", "input", "open", "range", "type", "write", "zeros", "acos", "asin", "atan", "cos", "e", "exp", "fabs", "floor", "log", "log10", "pi", "sin", "sqrt", "tan"]));

def encode_var_name(inp):
	if(inp[0] == '`' and inp[-1] == '`'):
		return "op_"+("".join(i if ((ord('A')<=ord(i)<=ord('Z')) or (ord('a')<=ord(i)<=ord('z'))) else "_"+str(ord(i))+"_" for i in inp[1:-1]));
	elif(inp in ["return", "print", "levels", "colnames"]):
		return inp;
	else:
		if(inp in must_transform):
			return must_transform[inp];
		else:
			return ""+inp.replace(".", "_");
		# return "v_"+inp.replace(".", "_");



def get_args(children):
	args = list(list(b) for a,b in itertools.groupby(children, lambda x: x["token"]=="','") if not(a));
	args1 = filter(lambda x: len(x) == 1, args);
	args2 = filter(lambda x: len(x) == 3, args);
	tmp= list(i[:-1]+[clean_tree2(i[-1], "expr")] for i in (args1 + args2));
	return tmp;

def split_list(l, checker):
	output = [];
	cur_elm = [];
	for i in l:
		if checker(i):
			output.append(cur_elm);
			cur_elm = [];
		else:
			cur_elm.append(i);
	output.append(cur_elm);
	return output;


def raw_text(inp):
	return dict(token="raw_text", children=[], text=inp);



def clean_tree2(subtree, tree_type):
	children = subtree['children'];
	if(subtree['token'] == 'exprlist'):
		output_list = [];
		output_element = [];
		good_expr = ['expr', 'exprlist', 'SYMBOL', "SYMBOL_FUNCTION_CALL", 'STR_CONST', 'NUM_CONST', 'SYMBOL_PACKAGE', "NEXT", "BREAK"];
		for i in children:
			if(i['token'] in good_expr and (len(i['children'])>0 or i['text'] != '')):
				if(len(output_element) > 0 and output_element[-1]['token'] in good_expr):
					output_list.append(output_element);
					output_element = [];
				output_element.append(i);
			elif(i['token'] in ["EQ_ASSIGN", "LEFT_ASSIGN", "RIGHT_ASSIGN"]):
				output_element.append(i);
		if(len(output_element) > 0):
			output_list.append(output_element);
			output_element = [];
		output_insts = [];
		for i in output_list:
			if len(i) == 1:
				if(i[0]['token'] == "exprlist"):
					output_insts += clean_tree2(i[0], tree_type);
				elif(i[0]['token'] in good_expr):
					output_insts += clean_tree2(i[0], "inst");
			elif len(i)==3:
				output_insts.append(dict(token="inst", inst_type="assign", children=[clean_tree2(i[0], "expr"), clean_tree2(i[2], "expr")]));
		return output_insts;
	elif(subtree['token'] == 'expr' and len(children)>0):
		if(children[0]['token']=="'{'" and children[-1]['token'] == "'}'"):
			return clean_tree2(dict(token="exprlist", children=children[1:-1]), "inst");
		elif(len(children) == 3 and children[0]['token'] == 'FOR'):
			return [dict(token="inst", inst_type="for", children=[clean_tree2(children[1], "expr"), clean_tree2(children[2], "inst")])];
		elif(len(children) == 5 and children[0]['token'] == 'WHILE'):
			return [dict(token="inst", inst_type="while", children=[clean_tree2(children[2], "expr"), clean_tree2(children[4], "inst")])];
		elif(len(children) == 2 and children[0]['token'] == 'REPEAT'):
			return [dict(token="inst", inst_type="while", children=[dict(token="raw_text", children=[], text="1"), clean_tree2(children[1], "expr")])];



		elif(len(children) in [5,7] and children[0]['token'] == 'IF'):
			return [dict(token="inst", inst_type="if", children=[clean_tree2(children[2], "expr"), clean_tree2(children[4], "inst"), (clean_tree2(children[6], "inst") if len(children)==7 else [])])];

		else:
			subexpr = None;
			if(children[0]['token'] == "'('" and children[-1]['token'] == "')'"):
				subexpr = dict(token="bracket", children=[clean_tree2(dict(token=subtree['token'], children=children[1:-1]), "expr")]);
			elif(children[0]['token'] == "FUNCTION"):
				state.lambda_function_id += 1;
				fun_name = "lambda_function_"+str(state.lambda_function_id);
				fun_args = get_args(children[2:-2]);
				fun_content = clean_tree2(children[-1], "inst");
				state.global_functions.append(dict(token="inst", inst_type="define", children=[fun_name, fun_args, fun_content]));
				subexpr = dict(token="raw_text", text=fun_name, children=[]);

			elif(len(children)>=3 and children[1]['token'] == "'['" and children[-1]['token'] == "']'" ):
				subexpr = dict(token="ARRAY_ACCESS", children=[clean_tree2(children[0], "expr"), list((raw_text("0") if (len(i)==0) else (clean_tree2(i[0], "expr"))) for i in split_list(children[2:-1], lambda x: x['token']== "','"))]);
			elif(len(children)>=3 and children[1]['token'] == "LBB" and children[-1]['token'] == "']'" ):
				subexpr = dict(token="ARRAY_ACCESS", children=[clean_tree2(children[0], "expr"), [dict(token="FUNCTION_CALL", children=[raw_text("py_list"), list([(raw_text("0") if (len(i)==0) else (clean_tree2(i[0], "expr")))] for i in split_list(children[2:-2], lambda x: x['token']== "','"))])]]);
			elif(len(children)>=3 and children[1]['token'] == "'('" and children[-1]['token'] == "')'" ):
				subexpr = dict(token="FUNCTION_CALL", children=[clean_tree2(children[0], "expr"), get_args(children[2:-1])]);

			elif(len(children) == 1):
				subexpr = dict(token="expr", children=[clean_tree2(children[0], "expr")]);
			elif(len(children) ==2 and children[0]['token'] in ["'-'", "'!'", "'~'", "'+'", "'?'"]):
				subexpr = dict(token="FUNCTION_CALL", children=[dict(token="raw_text", children=[], text=({"'-'": "neg", "'!'": "not", "'~'": "tilda", "'+'": "pos", "'?'": "question_mark"}[children[0]['token']])), [[clean_tree2(children[1], "expr")]]]);

			elif(len(children) == 3):

				symbol_mapping_left_op = {
					"'$'" : ".", 
				};

				symbol_mapping = soft_merge({
					"'^'": "**", 
					"GT": ">", 
					"LT": "<",
					"EQ": "==", 
					"LE": "<=", 
					"GE": ">=", 
					"NE": "!=", 
					"AND": "&", 
					"OR": "|", 
					"AND2": " and ", 
					"OR2": " or ", 
				}, dict(("'"+i+"'", i) for i in ["+", "-", "/", "*"]));

				symbol_fun = {"':'": "r_range", "IN": "belongs", "'~'": "tilda", "NS_GET": "ns_get", "'@'": "r_at_symbol"};
	
				if(children[1]['token'] in symbol_mapping):
					subexpr = dict(token="operator", operator=symbol_mapping[children[1]['token']], children=list(clean_tree2(children[i], "expr") for i in [0,2]));
				elif(children[1]['token'] in symbol_mapping_left_op):
					subexpr = dict(token="left_operator", operator=symbol_mapping_left_op[children[1]['token']], children=list(clean_tree2(children[i], "expr") for i in [0,2]));
				elif(children[1]['token'] in symbol_fun or children[1]['token'] == "SPECIAL"):
					subexpr = dict(token="FUNCTION_CALL", children=[dict(token="raw_text", text=(symbol_fun[children[1]['token']] if (children[1]['token'] != "SPECIAL") else encode_var_name("`"+children[1]['text']+"`")), children=[]), list([clean_tree2(children[i], "expr")] for i in [0,2])]);

				elif(children[1]['token'] in ['LEFT_ASSIGN', 'RIGHT_ASSIGN', "EQ_ASSIGN"]):
					if(tree_type == "inst"):
						subchildren = [clean_tree2(children[0], "expr"), clean_tree2(children[2], "expr")];
						if(children[1]['token'] == "RIGHT_ASSIGN"):
							subchildren = subchildren[::-1];
						return [dict(token="inst", inst_type="assign", children=subchildren)];
					elif(tree_type == "expr"):
						return dict(token="FUNCTION_CALL", children=[dict(token="raw_text", text="assign", children=[]), [[clean_tree2(children[0], "expr")], [clean_tree2(children[2], "expr")]]]);

			if(subexpr == None):
				print subtree;
				1/0;

			if(tree_type == "inst"):
				return [dict(token="inst", inst_type="expr", children=[subexpr])];
			else:
				return subexpr;
	elif(subtree["token"] == "forcond"):
		if(["'('", "SYMBOL", "IN", "expr", "')'"] == list(i['token'] for i in children)):
			return dict(token="forcond", children=[clean_tree2(children[1], "expr"), clean_tree2(children[3], "expr")]);

	else:
		return (subtree if tree_type == "expr" else [dict(token="inst", inst_type="expr", children=[subtree])]);



def tree2py(subtree):
	token = subtree['token'];
	children = subtree['children'];
	if(token == 'inst'):
		inst_type = subtree['inst_type'];
		if(inst_type == "assign"):
			return tree2py(children[0])+" = "+tree2py(children[1]);
		elif(inst_type == "expr"):
			return tree2py(children[0]);
		elif(inst_type == "for"):
			return ("for "+tree2py(children[0])+":", list(tree2py(i) for i in children[1]));
		elif(inst_type == "while"):
			return ("while "+tree2py(children[0])+":", list(tree2py(i) for i in children[1]));
		elif(inst_type == "if"):
			return ("if "+tree2py(children[0])+":", list(tree2py(i) for i in children[1]), "else:", list(tree2py(i) for i in children[2]));
		elif(inst_type == "define"):
			return ("def "+children[0]+"("+(", ".join(("" if len(i)==1 else tree2py(i[0])+"=")+tree2py(i[-1]) for i in children[1]))+"):", list(tree2py(i) for i in children[2]));

	elif(token in ["SYMBOL", "SYMBOL_FUNCTION_CALL", "SYMBOL_FORMALS", "SYMBOL_SUB", "SPECIAL", "SYMBOL_PACKAGE", "SLOT"]):
		return encode_var_name(subtree["text"]);
	elif(token in ["NUM_CONST", "STR_CONST", "raw_text"]):
		return subtree['text'];
	elif(token == 'left_operator'):
		return tree2py(children[0])+ subtree['operator'] + tree2py(children[1]);
	elif(token == 'operator'):
		return "("+tree2py(children[0])+ subtree['operator'] + tree2py(children[1])+")";
	elif(token == 'bracket'):
		return "("+tree2py(children[0])+")";
	elif(token == "expr"):
		return tree2py(children[0]);
	elif(token == "FUNCTION_CALL"):
		fun_def_exp = tree2py(children[0]);
		special_methods = ["colnames", "levels"];
		return fun_def_exp+["(", "["][fun_def_exp in special_methods]+(", ".join(("" if len(i)==1 else tree2py(i[0])+"=")+tree2py(i[-1]) for i in children[1]))+[")", "]"][fun_def_exp in special_methods];
	elif(token == "ARRAY_ACCESS"):
		return tree2py(children[0])+"["+(", ".join(tree2py(i) for i in children[1]))+"]";

	elif(token == "forcond"):
		return tree2py(children[0])+" in "+tree2py(children[1]);
	elif(token in ["NEXT", "BREAK"]):
		return {"NEXT": "continue", "BREAK": "break"}[token];

	else:
		return "None";


def write_py(instructions, write_to):
	fd = open(write_to, "w");
	def helper(instructions, depth):
		if(len(instructions) == 0):
			instructions = ["pass"];
		for i in instructions:
			if(type(i) == tuple):
				fd.write("  "*depth+str(i[0])+"\n");
				helper(i[1], depth+1);
				if(len(i)==4):
					fd.write("  "*depth+str(i[2])+"\n");
					helper(i[3], depth+1);
			else:
				fd.write("  "*depth+str(i)+";"+"\n");
			if(depth == 0):
				fd.write("\n");
	helper(instructions, 0);
	fd.close();



def print_py(instructions, depth=0):
	if(len(instructions) == 0):
		instructions = ["pass"];
	for i in instructions:
		if(type(i) == tuple):
			print "  "*depth+str(i[0]);
			print_py(i[1], depth+1);
			if(len(i)==4):
				print "  "*depth+str(i[2]);
				print_py(i[3], depth+1);

		else:
			print "  "*depth+str(i)+";";
		if(depth == 0):
			print;


def get_str(subtree):
	if(len(subtree['children']) == 0):
		output = [json.dumps(subtree['text'])];
	else:
		output = list(get_str(indexed_parsed_code[x]) for x in subtree['children']);
	output = [str(subtree["id"])+str(subtree['token'])] + output;
	return " ( "+", ".join(output)+" ) ";

def get_str1(subtree):
	if(len(subtree['children']) == 0):
		output = [json.dumps(subtree['text'])];
	else:
		output = list(get_str1(indexed_parsed_code[x]) for x in subtree['children']);
	return {"node": subtree['text']+"("+str(subtree["id"])+","+str(subtree['token'])+")", "children": output};



def test(input_file="student.r"):
	input_and_init(input_file);
	create_graph();
	topological_sorting();
	create_parent_relation();
	write_file("test_parsed_tree.data.py", get_str(indexed_parsed_code[0]));
	write_file("test_parsed_tree.data1.py", json.dumps(get_str1(indexed_parsed_code[0])));
	tree1 = clean_tree1(indexed_parsed_code[0]);

	# print tree1;

	ans = clean_tree2(tree1, "inst");

	ans = state.global_functions + ans;

	# print tree1;

	# print "ans =";
	# for i in ans:
	# 	print i;
	# print "ans-end";

	ans1 = list(tree2py(i) for i in ans);

	print_py(ans1);




def r2py(inp, outp):
	output = dict(status=1);
	log("Processing: "+inp);
	try:
		input_and_init(inp);
		create_graph();
		topological_sorting();
		create_parent_relation();
		tree1 = clean_tree1(indexed_parsed_code[0]);
		ans = clean_tree2(tree1, "inst");
		ans = state.global_functions + ans;
		ans1 = list(tree2py(i) for i in ans);
		write_py(ans1, outp);
		log("Successfully Finished "+inp+"\nWritting at "+outp);
	except Exception as e:
		log("Failed "+inp+"\nDue to error: "+str(e));
		output['status'] = -1;
	return output;


def r2py_recursive(inp, outp, limit=100000):
	all_files = Help.list_file_recursive(inp);
	for i in all_files[:limit]:
		if(i.split(".")[-1].lower() == "r"):
			outp_file = outp+i[len(inp):];
			if(not(os.path.isdir(os.path.dirname(outp_file)))):
				os.makedirs(os.path.dirname(outp_file));
			r2py(inp+i, outp_file);


def script():
	all_files = Help.list_files("../assignments/assign2_clean_r/");
	print all_files;
	faltu_files = ["20915.R", "26694.R", "29280.R", "8938.R"];
	# faltu_files = ["73118.R", "9010.R"];
	for i in all_files[99:]:
		if(i.split(".")[-1] == "R" and i not in faltu_files):
			print time.time();
			r2py("../assignments/assign2_clean_r/"+i, "../assignments/assign2_py/"+i.split(".")[0]+".py");
	print time.time();
	print "Done - All";



# script();

# r2py("student.r", "student.py");

# test("../assignments/new_r_file/9010.R");
# test("../assignments/new_r_file/8909.R");



