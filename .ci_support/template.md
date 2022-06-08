# List of Packages 

| Package Name | Downloads |
|:-------------|:---------:|
{% for package in package_lst -%}
| [{{ package }}](https://anaconda.org/conda-forge/{{ package }}) | [![conda](https://anaconda.org/conda-forge/{{ package }}/badges/downloads.svg)](https://anaconda.org/conda-forge/{{ package }}) |
{% endfor %}
