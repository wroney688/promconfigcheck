# Prometheus Config Checking Demo
Uses a Flask based app to act as a configuration scraper.  Exposes information to Prometheus for scraping

How to use:
python (v3x) promconfigcheck.py

point to http://<host>:9270(configurable in .py)/metrics

Looks for *.model in the execution directory.  The model file starts with a line: `compareTo(XML): target.xml` and then a fragment to compare.  Expand the (XML) to include other types accordingly.  XML was provided to illustrate the method.

A single rule can be created (assumes the scraping rule adds job/instance labels):
```
groups:
- name: MyAppConfigCheck
  rules:
    - alert: AutomatedConfigCheck
    expr: configcheck == 0
    for: 1m
    labels:
      severity: triage
    annotations:
      description: "Configuration Mismatch ==>  target {{ $labels.instance }} of job {{ $labels.job }} does not appear to be correct for {{ $labels.path }} ."  
```

Example file result on the /metric endpoing
```
<removed the flask entries>

# HELP configcheck Config Match==1, Mismatch==0
# TYPE configcheck gauge
configcheck{configfile="exampleconfig.xml",path="xml.tag"} 1.0
configcheck{configfile="exampleconfig.xml",path="xml.backends.be(instance3)"} 1.0
configcheck{configfile="exampleconfig.xml",path="xml.pool[name=db, target=db3](10)"} 0.0
```
#Compare Formats:
## XML
compareTo(XML): <filename>

Remainder of the file is an xml model.  
## OS
compareTo(OS): localhost

Remainder of the file is YAML with the following model
```
OS_Values:
-  name:
   command:
   regex:
```
Will spit out a configcheck metric with path=<name>.  The value will be based upon whether the execution of <command> matches the regular expression <regex>
