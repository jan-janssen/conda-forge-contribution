import sys
import getopt
import requests
import pandas
from datetime import date
from jinja2 import Template
from urllib.error import URLError


query_template = """
{
  organization(login: "conda-forge") {
{%- if after %}
    teams(first: 100, after: "{{ after }}", userLogins: ["{{ githubuser }}"]) {
{%- else %}
    teams(first: 100, userLogins: ["{{ githubuser }}"]) {
{%- endif %}
      totalCount
      edges {
        node {
          name
          description
        }
      }
      pageInfo {
        endCursor
        hasNextPage
      }
    }
  }
}
"""


def get_all_package_names(username, token):
    t = Template(query_template)
    after = None 
    next_page = True 
    packages_lst = []
    while next_page: 
        query = t.render(githubuser=username, after=after)
        request = requests.post('https://api.github.com/graphql', json={'query': query}, headers={"Authorization": token})
        if request.status_code == 200:
            result_dict = request.json()
        else:
            raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))
        next_page = result_dict['data']['organization']['teams']['pageInfo']['hasNextPage']
        after = result_dict['data']['organization']['teams']['pageInfo']['endCursor']
        for n in result_dict['data']['organization']['teams']['edges']:
            if n['node']['name'] not in ['all-members', 'Core']:
                packages_lst.append(n['node']['name'])
    return packages_lst


def read_template(file):
    with open(file, 'r') as f:
        return f.read()


def write_index(file, output):
    with open(file, 'w') as f: 
        f.writelines(output)


def write_files(total_packages):
    web = Template(read_template(file=".ci_support/template.html"))
    web_output = web.render(package_lst=total_packages)
    write_index(file="index.html", output=web_output)
    md = Template(read_template(file=".ci_support/template.md"))
    md_output = md.render(package_lst=total_packages)
    write_index(file="packages.md", output=md_output)


def command_line(argv):
    username = None
    token = None
    repo = None
    try:
        opts, args = getopt.getopt(
            argv[1:], "u:t:g:h", ["username=", "token=", "githubrepo=", "help"]
        )
    except getopt.GetoptError:
        print("run.py -u <username> -t <token> -g <githubrepo>")
        sys.exit()
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print("run.py -u <username> -t <token> -g <githubrepo>")
            sys.exit()
        elif opt in ("-u", "--username"):
            username = arg
        elif opt in ("-t", "--token"):
            token = arg
        elif opt in ("-g", "--githubrepo"):
            repo = arg 
    return username, token, repo


def get_download_count_line(content_lst):
    for i, l in enumerate(content_lst):
        if "total downloads" in l:
            return int(l.split(">")[1].split("<")[0])


def get_github_stats_url(repo, filename):
    username, reponame = repo.split("/")
    return "http://" + username + ".github.io/" + reponame + "/" + filename
    

def get_package_download_count(package_name):
    r = requests.get('https://anaconda.org/conda-forge/' + package_name)
    return get_download_count_line(content_lst=r.content.decode().split("\n"))


def get_condaforge_contribution(package_lst):
    download_count_lst = [get_package_download_count(package_name=p) for p in package_lst]
    
    # Number of packages
    package_lst.append("number")
    download_count_lst.append(len(package_lst))
    
    # Sum number of downloads 
    package_lst.append("sum")
    download_count_lst.append(sum([v for v in download_count_lst if v is not None]))
    
    # Prepend date 
    package_lst.insert(0, "Date")
    download_count_lst.insert(0, date.today().strftime("%Y/%m/%d"))
    
    return pandas.DataFrame({p:[d] for p, d in zip(package_lst, download_count_lst)})


def download_existing_data(data_download):
    try:
        return pandas.read_csv(data_download, index_col=0)
    except URLError:  # this is the case for the first built
        return pandas.DataFrame({})


def get_statistics(package_lst, repo, filename):
    pandas.concat([
        download_existing_data(data_download=get_github_stats_url(
            repo=repo, 
            filename=filename,
        )), 
        get_condaforge_contribution(package_lst=package_lst),
    ], sort=False).to_csv(filename)


if __name__ == "__main__":
    username, token, repo = command_line(sys.argv)
    package_lst = get_all_package_names(username=username, token="bearer "+token)
    write_files(total_packages=package_lst)
    get_statistics(
        package_lst=package_lst,
        repo=repo,
        filename="stats.csv"
    )
