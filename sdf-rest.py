from bottle import route, run, debug, template, request
import shlex
import sqlite3
from subprocess import call, Popen, PIPE

@route('/new', method='POST')
def newTest():
    new = request.body.read()
    conn = sqlite3.connect('tests.db')
    c = conn.cursor()

    c.execute("INSERT INTO tests (name) VALEUS (?)", (new,))
    new_id = c.lastrowid

    conn.commit()
    c.close()

    return '</p> New test saved with ID %s</p>' % new_id

@route('/listOVLiveDiagTestsOnPod/<pod>')
def listTests(pod):
    conn = sqlite3.connect('tests.db')
    c = conn.cursor()
    c.execute("SELECT * FROM tests")
    result = c.fetchall()
    c.close()

    output = template('make_table', rows=result)
    return output

@route('/listOVLiveDiagTestsOnPod/<pod>/JSON')
def listTestsJSON(pod):
    conn = sqlite3.connect('tests.db')
    c = conn.cursor()
    c.execute("SELECT * FROM tests")
    result = c.fetchall()
    c.close()
    tests = [i[1] for i in result]

    jason = dict({"OV Live List of Diagnostic Tests on Pod": {}})
    for i in range(len(tests)):
        jason["OV Live List of Diagnostic Tests on Pod"][i] = tests[i]

    return jason

@route('/run/OVLivePodNodePairPerfTest/<node1>/<node2>')
def runPerf(node1, node2):
    p1 = Popen(["iperf3", "-s", "-p", "2018", "-1"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    p2 = Popen(["iperf3", "-c", "192.168.64.130", "-p", "2018"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output, err = p2.communicate(b"input data that is passed to subprocess")
    rc = p2.returncode
    code = "PASS" if err == '' else "FAIL"
    status = "Node \"" + str(node1) + "\" and Node \"" + str(node2) + "\" Connection Successful"
    details = output
    json = {"OVLive Pod Node Pair iPerf Test": {"Result Code": code, "Result Status": status, "Result Details": details}}
    return json

@route('/run/util/<node>')
def runUtil(node):
    inp = ["top", "-b", "-n", "2", "|", "grep", "-i", "\"Cpu(s)\"", "|", "cut", "-d", "' '", "-f11", "|", "awk",
            "'{p = 100-$1} END {print p, \"% CPU Usage\"}\'", ";", 
            "top", "-b", "-n", "1", "|", "grep", "-i", "\"Mem\"", "-m", "1", "|", "awk",  
            "\'{print ($8/$4*100), \"% Mem Used,\", ($6*(2^10)/(10^9)), \"GB Used /\", ($4*(2^10)/(10^9)), \"GB Total\"}"]

    inp2 = ["top", "-b", "-n", "2", "|", "grep", "-i", "\"Cpu(s)\"", "|", "cut", "-d", "' '", "-f11", "|", "awk",
            "'{p = 100-$1} END {print p, \"% CPU Usage\"}\'"]

    inp3 = "top -b -n 2|grep -i \"Cpu(s)\" | cut -d ' ' -f11 | awk '{p = 100-$1} END {print p,\"% CPU Usage\"}' ; top -b -n 1|grep -i \"Mem\" -m 1| awk '{print ($8/$4*100), \"% Mem Used,\", ($6*(2^10)/(10^9)), \"GB Free /\", ($4*(2^10)/(10^9)), \"GB Total\"}' ; top -b -n 1|grep -i \"Swap\" -m 1| awk '{print ($7/$3*100), \"% Swap Mem Used,\", ($5*(2^10)/(10^9)), \"GB Free /\", ($3*(2^10)/(10^9)), \"GB Total\"}'"

    top1_args = ["top", "-b", "-n", "2"]
    grep1_args = ["grep", "-i", "\"Cpu(s)\""]
    cut1_args = ["cut", "-d", "\' \'", "-f11"]
    awk1_args = ["awk", "'{p = 100-$1} END {print p, \"% CPU Usage\"}'"]

    top2_args = ["top", "-b", "-n", "1"]
    grep2_args = ["grep", "-i", "\"Mem\"", "-m", "1"]
    awk2_args = ["awk", "{print ($8/$4*100), \"% Mem Uses,\", ($6*(2^10)/(10^9)), \"GB Used /\", ($4*(2^10)(10^9)), \"GB Total\"}"]

    '''
    ps_top1 = Popen(top1_args, stdout=PIPE, stderr=PIPE, shell=False)
    ps_grep1 = Popen(grep1_args, stdin=ps_top1.stdout, stdout=PIPE, shell=False)
    ps_cut1 = Popen(cut1_args, stdin=ps_grep1.stdout, stdout=PIPE, shell=False)
    ps_awk1 = Popen(awk1_args, stdin=ps_cut1.stdout, stdout=PIPE, shell=False)
    
    ps_top1.stdout.close()
    ps_grep1.stdout.close()
    ps_cut1.stdout.close()

    ps_top2 = Popen(top2_args, stdout=PIPE, stderr=PIPE, shell=False)
    ps_grep2 = Popen(grep2_args, stdin=ps_top2.stdout, stdout=PIPE, shell=False)
    ps_awk2 = Popen(awk2_args, stdin=ps_grep2.stdout, stdout=PIPE, shell=False)
    ps_top2.stdout.close() 
    ps_grep2.stdout.close()
    '''
    
    p = Popen(inp3, stdout=PIPE, stderr=PIPE, shell=True)
    out, err = p.communicate(b"input data that is passed to subprocess")
    rc = p.returncode
    return out

@route('/run/endpointHealth')
def runEndpoints():
    endpoints = ['2018', '2009', '2020', '8081', '3456']
    out = []
    '''
    for i in range(len(endpoints)-1):
        serve_start = Popen(shlex.split("python -m SimpleHTTPServer 2018"), stdout=PIPE, shell=False)
        servers.append(serve_start)
    
    for end in endpoints:
        attempt = Popen(shlex.split("curl localhost:"+end), stdout=PIPE, shell=False)
        res = attempt.communicate()[0]
        out.append(res)
        '''

    passes = []
    for end in endpoints:
        p = Popen(shlex.split("curl localhost:"+end), stdout=PIPE, shell=False)
        res = p.communicate()
        if res[0] == '':
            passes.append(False)
            out.append("Port["+end+"]: Fail\n")
        else:
            passes.append(True)
            out.append("Port["+end+"]: Success\n")

    code = "PASS" if all(passes) else "FAIL"
    status = str(sum(passes)) + "/" + str(len(passes)) + " Connections Successful"
    json = {"OVLive Pod Service Endpoint Health Check": {"Result Code": code, "Result Status": status, "Result Details": out}}
    return json

@route('/run/certificate')
def runCertificateCheck():
    p = Popen(shlex.split("openssl s_client -showcerts -connect localhost:2018"), stdout=PIPE, shell=False)
    out = p.communicate()[0]
    # Verify return code: 
    code = "PASS" if ok in out[558:out.find("Extended", 538)] else "FAIL"
    status = "todo"
    json = {"OVLive Pod Service Get Certificate Expiry Health Status": {"Result Code": code, "Result Status": status, "Result Details": out}}
    return out

@route('/run/docker')
def runDocker():
    p = Popen(shlex.split("systemctl is-active docker"), stdout=PIPE, shell=False)
    out = p.communicate()[0]

    code = "FAIL" if inactive in out else "PASS"
    status = code
    details = "docker inactive" if code == "FAIL" else "docker active"

    return out


run(host='0.0.0.0', port=8080, debug=True)
