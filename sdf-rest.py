import bottle
from bottle import route, run, debug, template, request, error, redirect, response
import sys
import shlex
import sqlite3
from subprocess import call, Popen, PIPE

avail_tests = ["OVLivePodNodePairPerfTest", "OVLiveEndpointHealthCheck", "OVLiveCertificateExpiryTest"]

@route('/new', method='POST')
def newTest():
    new = request.body.read()
    conn = sqlite3.connect('tests.db')
    c = conn.cursor()

    c.execute("INSERT INTO tests (name) VALUES (?)", (new,))
    new_id = c.lastrowid

    conn.commit()
    c.close()

    return '</p> New test saved with ID %s</p>' % new_id

@route('/hello')
def hello():
    return "\nSDF-Service Running. Use \"/listOVLiveDiagTestsOnPod\" for available diagnostic tests.\n"

@route('/listPodTests/html')
@route('/listOVLiveDiagTestsOnPod/html')
@route('/listovlivediagtestsonpod/html')
def listTests():
    output = template('make_table', rows=avail_tests)
    return output

@route('/listPodTests')
@route('/listOVLiveDiagTestsOnPod')
@route('/listovlivediagtestsonpod')
def listTestsJSON():
    # tests = [i[1] for i in result]

    jason = dict({"OV Live List of Diagnostic Tests on Pod": {}})
    for i in range(len(avail_tests)):
        jason["OV Live List of Diagnostic Tests on Pod"][i] = avail_tests[i]

    return jason

@route('/test/<node1>/<node2>')
def iptest(node1, node2):
    return (node1, node2)

@route('/perf/run/<node1>/<node2>')
@route('/OVLivePodNodePairPerfTest/run/<node1>/<node2>')
@route('/ovlivepodnodepairperftest/run/<node1>/<node2>')
def runPerf(node1, node2):
    fire1 = Popen(shlex.split("ssh -o ConnectTimeout=10 -o BatchMode=yes -o StrictHostKeyChecking=no -i .ssh/vos-bm-poc.pem centos@"+node1+" \"sudo firewall-cmd --zone=public --add-port=2018/tcp --permanent ; sudo firewall-cmd --reload\""), stdout=PIPE, shell=False) 
    fireout1 = fire1.communicate()[0]

    fire2 = Popen(shlex.split("ssh -o ConnectTimeout=10 -o BatchMode=yes -o StrictHostKeyChecking=no -i .ssh/vos-bm-poc.pem centos@"+node2+" \"sudo firewall-cmd --zone=public --add-port=2018/tcp --permanent ; sudo firewall-cmd --reload\""), stdout=PIPE, shell=False) 


    setup1 = Popen(shlex.split("ssh -o ConnectTimeout=10 -o BatchMode=yes -o StrictHostKeyChecking=no -i .ssh/vos-bm-poc.pem centos@"+node1+" sudo yum install iperf3 -y"), stdout=PIPE, shell=False)
    out0, err0 = setup1.communicate()
    if err0 == None : err0 = "No Err"

    setup2 = Popen(shlex.split("ssh -o ConnectTimeout=10 -o BatchMode=yes -o StrictHostKeyChecking=no -i .ssh/vos-bm-poc.pem centos@"+node2+" sudo yum install iperf3 -y"), stdout=PIPE, shell=False)
    out02, err02 = setup2.communicate()
    if err02 == None: err0 = "No Err"

    n1 = Popen(shlex.split("ssh -o ConnectTimeout=10 -o BatchMode=yes -o StrictHostKeyChecking=no -i .ssh/vos-bm-poc.pem centos@"+node1+" iperf3 -s -p 2018 -1 -D"), stdout=PIPE, shell=False)
    # n1_serve = Popen(shlex.split("1"), stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=False)
    
    out1 = n1.communicate()[0]

    n2 = Popen(shlex.split("ssh -o ConnectTimeout=10 -o BatchMode=yes -o StrictHostKeyChecking=no -i .ssh/vos-bm-poc.pem centos@"+node2+" iperf3 -c "+node1+" -p 2018"), stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=False)
    # n2_conn = Popen(shlex.split("iperf3 -c "+node1+" -p 2018"), stdin=PIPE, stdout=PIPE, stderr=PIP, shell=False)

    output, err = n2.communicate(b"input data that is passed to subprocess")
    rc = n2.returncode

    
    code = "PASS" if err == '' else "FAIL"
    status = "Node \"" + str(node1) + "\" and Node \"" + str(node2) + "\" Connection Successful"
    details = output
    json = {"OVLive Pod Node Pair iPerf Test": {"Result Code": code, "Result Status": status, "Result Details": details}}
    return output
    return json

@route('/perf/local/run')
def localPerf():
    p1 = Popen(shlex.split("iperf3 -s -p 2010 -1"), stdin=PIPE, stdout=PIPE, stderr=PIPE)
    p2 = Popen(shlex.split("iperf3 -c 127.0.0.1 -p 2010 | json_pp -t json"), stdin=PIPE, stdout=PIPE, stderr=PIPE)

    out1 = p2.communicate()[0]
    
    output, err = p2.communicate(b"input data that is passed to subprocess")
    rc = p2.returncode
    code = "PASS" if err == '' else "FAIL"
    status = " Connection Successful"
    details = output
    json = {"OVLive Pod Node Pair iPerf Test": {"Result Code": code, "Result Status": status, "Result Details": details}}
    return json

@route('/pairPerf/help')
@route('/OVLivePodNodePairPerfTest/help')
@route('/ovlivepodnodepairperftest/help')
def perfHelp():
    return """Usage: /run/OVLivePodNodePairPerfTest/<node1>/<node2>\n 
            node1 = IP address of first node in pair to check connection\n
            node2 = IP address of other node in pair to check connection\n\n
            You may also use the short-hand /run/pairPerf/<node1><node2>
            for the same results."""

@route('/run/util/<node>')
@route('/OVLiveNodeUtilizationCheck/run/<node>')
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
@route('/run/OVLiveEndpointHealthCheck')
def runEndpoints():
    endpoints = ["10.27.234.201", "10.27.234.202", "10.27.234.203", "10.27.234.204", "10.27.234.205", "10.27.234.206", "10.27.234.207",
                 "10.27.234.208", "10.27.234.209", "10.27.234.210", "10.27.234.211", "10.27.234.212", "10.27.234.213",
                 "10.27.234.214", "10.27.234.215"]
    out = []

    passes = []
    for end in endpoints:
        p = Popen(shlex.split("ping -c 1 -w 3 "+end), stdout=PIPE, shell=False)
        res = str(p.communicate()[0])
	
        loss = res[res.find(" ", res.find("% packet loss")-3)+1:res.find("% packet loss")]

        if int(loss) == 0:
            passes.append(True)
            out.append(end+": Connection Success\n")
        else:
            passes.append(False)
            out.append(end+": Connection Success\n")

    code = "PASS" if all(passes) else "FAIL"
    status = str(sum(passes)) + "/" + str(len(passes)) + " Connections Successful"
    json = {"OVLive Pod Service Endpoint Health Check": {"Result Code": code, "Result Status": status, "Result Details": out}
           }
    return json

@route('/help/endpointHealth')
@route('/help/OVLiveCheckEndpointHealthCheck')
def endpointHealthHelp():
    return """
Usage:  /run/OVLiveCheckEndpointHealthTest\n
Returns JSON of resullts\n
Result Code will be PASS if all endpoints are healthy, FAIL otherwise
Result Status will display number of healthy endpoints out of total
Result Details will contain the details of which endpoints are healthy or not\n
"""

@route('/run/certificate')
@route('/run/OVLiveCertificateExpiryTest')
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

@error(404)
def error404(error):
    return "Wrong URL"
    return redirect("/hello")

def fix_environ_middleware(app):
    def fixed_app(environ, start_response):
        environ['wsgi.url_scheme'] = 'https'
        environ['HTTP_X_FORWARDED_HOST'] = '10.27.204.232:8080'
        return app(environ, start_response)
    return fixed_app


app = bottle.default_app()
app.wsgi = fix_environ_middleware(app.wsgi)

portnum = 8080 if len(sys.argv) < 2 else sys.argv[1]
run(host='0.0.0.0', port=portnum, debug=True)
sys.exit(1)
