from flask import Flask, Response, request
from prometheus_client import generate_latest, Info, Gauge, Histogram, Counter, Summary, CONTENT_TYPE_LATEST, start_http_server
from prometheus_flask_exporter import PrometheusMetrics
import time, subprocess, yaml, re, glob, getopt, sys, threading, atexit
import xml.etree.ElementTree as etree

METRIC_PREFIX = 'configcheck'
PORT=9270


app = Flask(__name__)
m = PrometheusMetrics(app=app)
configCheck = Gauge('{0}'.format(METRIC_PREFIX), 'Config Match==1, Mismatch==0', ['configfile', 'path'])

def readModel(modelFile):
    fd = open(modelFile, "r")
    targetline = fd.readline()
    target = re.match("compareTo\((XML)\):\W*(.*)", targetline)
    if target is not None:
        if target.groups()[0] == 'XML': spec = etree.XML(fd.read())
        else: spec = None
        return target.groups()[0], target.groups()[1], spec
    else:
        return None, None, None

def removeNamespace(txt):
    return re.match('({.+})*(.+)',txt).groups()[1]

def formattedAttributes(myAttr):
    fStr = ''
    if len(myAttr) > 0:
        fStr = '[{0}]'.format(', '.join(myAttr))
    return fStr

def formattedValue(myVal):
    fStr = ''
    if myVal is not None and myVal.strip() != "":
        fStr = '({0})'.format(myVal.strip())
    return fStr

def recursiveFlatten(xml):
    children = list(xml)
    leaves = []
    subleaves = []
    myVal = xml.text
    myAttribs = []
    if xml.text is not None: #clean up whitespace
        myVal = xml.text.strip()
    for n, v in xml.attrib.items():
        cleanname = removeNamespace(n)
        if cleanname != 'schemaLocation': # intentionally omit this tag
            myAttribs.append('{0}={1}'.format(cleanname, v))
    prefix = '{0}{1}'.format(removeNamespace(xml.tag), formattedValue(myVal))
    if len(children) == 0:
        return ['{0}{1}{2}'.format(removeNamespace(xml.tag), formattedAttributes(myAttribs), formattedValue(myVal))]
    else:
        for child in children:
            subleaves.append(', '.join(recursiveFlatten(child)))
    for leaf in subleaves: #prepend my prefix
        leaves.append('{0}{1}.{2}'.format(prefix, formattedAttributes(myAttribs), leaf))
    return leaves

def compareXML(configName, model, actual):
    flatModel = recursiveFlatten(model)
    flatActual  = recursiveFlatten(actual)
    for entry in flatModel:
        if entry in flatActual:
            configCheck.labels(configName, '{0}'.format(entry)).set(1)
        else:
            configCheck.labels(configName, '{0}'.format(entry)).set(0)
    return

userID = None
osMetrics = {}

def grabOSData():
    return

def updateConfigReport():
    for model in [file for file in glob.glob('./*.model')]:
        print('\tChecking [{0}]'.format(model))
        type, target, spec = readModel(model)
        if type == 'XML': compareXML(target, spec, etree.XML(open(target, "r").read()))
        else: print('{0} is invalid.'.format(model))

    grabOSData()

@app.route('/metrics', methods=['GET'])
def metrics():
    updateConfigReport()
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == '__main__':
    argv = sys.argv[1:]
    opts, args = getopt.getopt(argv, 'u:')
    for opt in opts:
        if opt[0] == '-u': userID = opt[1]

    print('OS UID: {0}'.format(userID))
    app.run(debug=True, host='0.0.0.0', port=PORT)
