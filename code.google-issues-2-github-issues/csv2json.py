import sys
import csv
import json
import unicodedata
import requests
from lxml import html

def extract_project_labels(str):
    text = unicodedata.normalize('NFKD', str).encode('ascii', 'ignore')
    labels = text.strip().split(",")

    project = []

    # remove empty and non project label-s like Type-, Priority-
    for label_text in labels:
        label = label_text.strip()
        if len(label) == 0:
            continue

        if label.find("Type") > -1:
            continue

        if label.find("Priority") > -1:
            continue

        project.append(label)

    # TODO: do it properly/cleanly
    # remove synonyms like SpatialPortal Spatial-Portal, replacing it with one label: SpatialPortal
    if "Spatial-Portal" in project:
        project.pop(project.index("Spatial-Portal"))
        if not "SpatialPortal" in project:
            project.append("SpatialPortal")

    return project

def get_issue_details(id):
    page = requests.get("https://code.google.com/p/ala/issues/detail?id=" + id)
    tree = html.fromstring(page.text)

    # issue description, id="hc0"
    details = tree.xpath('//div[@class="cursor_off vt issuedescription"]/pre/text()')

    # issue comments, id="hc1", "hc2", "hc3" and so on
    # '//div[@class="cursor_off vt issuedescription"]/pre/i/text()' => <pre><i>(No comments)</i></pre>
    # '//div[@class="cursor_off vt issuecomment"]/pre/a/@href' => link in format '/p/ala/issues/detail?id=434' is link to other issue

    comments = tree.xpath('//div[@class="cursor_off vt issuecomment"]')
    for comment in comments:
        print 'comment id: {}'.format(comment.xpath('@id'))
 
    return details

def create_json(file_name, column_names):
    csv_file = open(file_name[0], 'r')

    csv_reader = csv.DictReader(csv_file, column_names) 
    out = json.dumps( [row for row in csv_reader] )

    data = json.loads(out)
    #print "number of issues found: %d" % len(data)

    # simple report in HTML format into stdout
    print '<html>'
    print '<body>'
    print '<table border="1">'

    for issue in data:

        project = extract_project_labels(issue["AllLabels"]);

        # for issues that have 0 or multiple number of projects, print them out:
        if len(project) != 1:
            #print 'id: {}, project_label({}): {}'.format(issue["ID"], len(project), project)
            if len(project) == 0:
                err = "NO PROJECT"
            
            if len(project) > 1:
                err = "MULTIPLE ({}) PROJECTS".format(project);
            print '<tr><td>{}</td><td>{}</td><td><a href="https://code.google.com/p/ala/issues/detail?id={}">{}</a></td></tr>'.format(issue["ID"], err, issue["ID"], issue["Summary"])
        else:
            issue["project"] = project[0]
            issue["details"] = get_issue_details(issue["ID"])

    print '</table>'
    print '</body>'
    print '</html>'

    out = json.dumps(data, sort_keys=True)

    json_file = open(file_name[0] + ".json", 'w')
    json_file.write(out);

if __name__=="__main__":
        create_json(sys.argv[1:], ["ID","Type","Status","Priority","Owner","Summary","AllLabels","Modified","ModifiedTimestamp"])
