import sys
import getopt
import requests
import pandas
from typing import List
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


def get_all_package_names(username: str, token: str) -> list:
    """
    Retrieves a list of all package names for a given user from the GitHub API.

    Args:
        username (str): The GitHub username.
        token (str): The GitHub API token.

    Returns:
        list: A list of package names.

    Raises:
        Exception: If the query fails to run.
    """
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


def read_template(file: str) -> str:
    """
    Reads the content of a file and returns it as a string.

    Args:
        file (str): The path to the file.

    Returns:
        str: The content of the file as a string.
    """
    with open(file, 'r') as f:
        return f.read()


def write_index(file: str, output: str) -> None:
    """
    Writes the output to a file.

    Args:
        file (str): The path to the file.
        output (str): The content to write.
    """
    with open(file, 'w') as f: 
        f.writelines(output)


from typing import List

def write_files(total_packages: List[str]) -> None:
    """
    Write files for the given list of packages.

    Args:
        total_packages (List[str]): A list of package names.
    """
    web = Template(read_template(file=".ci_support/template.html"))
    web_output = web.render(package_lst=total_packages)
    write_index(file="index.html", output=web_output)
    md = Template(read_template(file=".ci_support/template.md"))
    md_output = md.render(package_lst=total_packages)
    write_index(file="packages.md", output=md_output)


def command_line(argv):
    """
    Parses the command line arguments and returns the username, token, and repo.

    Args:
        argv (List[str]): The command line arguments.

    Returns:
        Tuple[str, str, str]: A tuple containing the username, token, and repo.

    Raises:
        GetoptError: If there is an error parsing the command line arguments.
    """
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


def get_download_count_line(content_lst: List[str]) -> int:
    """
    Get the line containing the total download count from the given list of strings.

    Args:
        content_lst (List[str]): The list of strings to search in.

    Returns:
        int: The total download count.

    """
    for i, l in enumerate(content_lst):
        if "total downloads" in l:
            return int(l.split(">")[1].split("<")[0])


def get_github_stats_url(repo: str, filename: str) -> str:
    """
    Returns the URL for the GitHub stats page for a given repository and filename.

    Args:
        repo (str): The repository in the format "username/reponame".
        filename (str): The name of the file.

    Returns:
        str: The URL for the GitHub stats page.
    """
    username, reponame = repo.split("/")
    return "http://" + username + ".github.io/" + reponame + "/" + filename
    

def get_package_download_count(package_name: str) -> int:
    """
    Get the download count for a given package from the conda-forge channel.

    Args:
        package_name (str): The name of the package.

    Returns:
        int: The download count for the package.
    """
    r = requests.get('https://anaconda.org/conda-forge/' + package_name + '/manage')
    return get_download_count_line(content_lst=r.content.decode().split("\n"))


def get_condaforge_contribution(package_lst: List[str]) -> pandas.DataFrame:
    """
    Get the contribution of Conda Forge packages.

    Args:
        package_lst (List[str]): List of package names.

    Returns:
        pandas.DataFrame: DataFrame containing the package names and their download counts.

    """
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


def download_existing_data(data_download: str) -> pandas.DataFrame:
    """
    Downloads existing data from the given data_download URL and returns it as a pandas DataFrame.

    Args:
        data_download (str): The URL of the data to be downloaded.

    Returns:
        pandas.DataFrame: The downloaded data as a pandas DataFrame.

    Raises:
        URLError: If there is an error in downloading the data.

    """
    try:
        return pandas.read_csv(data_download, index_col=0)
    except URLError:  # this is the case for the first built
        return pandas.DataFrame({})


def get_statistics(package_lst: list, repo: str, filename: str) -> None:
    """
    Get statistics for a given package list, repository, and filename.

    Parameters:
    - package_lst (list): A list of packages.
    - repo (str): The repository name.
    - filename (str): The name of the output file.

    Returns:
    None
    """
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
