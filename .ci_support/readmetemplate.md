# conda-forge-contribution
[![Deploy](https://github.com/jan-janssen/conda-forge-contribution/workflows/Deploy/badge.svg)](https://github.com/jan-janssen/conda-forge-contribution/actions)

This repository allows you to quickly generate a list of all your [conda-forge](https://conda-forge.org) contributions.

For example the contributions of [jan-janssen](https://github.com/jan-janssen) are available at [https://jan-janssen.github.io/conda-forge-contribution/](https://jan-janssen.github.io/conda-forge-contribution/).

To generate your own contribution-list, simply fork this repository and set the environment variable `GH_TOKEN` as a [github action secret](https://docs.github.com/en/actions/reference/encrypted-secrets#creating-encrypted-secrets-for-a-repository):

```
GH_TOKEN = <your Github token which enables access to public_repo and read:org>
```

For the token the following permissions are required:
![Required Permissions](permissions.png)

After creating the environment variable `GH_TOKEN` trigger a new build on the master branch. 

Designed by [colorlib](https://colorlib.com/wp/template/responsive-table-v2/).
