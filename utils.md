# Just a md to store some useful information

## DicomWeb
https://www.dicomstandard.org/using/dicomweb
https://www.dicomstandard.org/using/dicomweb/restful-structure

## Black (Code Formatter)
```black .```
or
```black src/app/main.py```

## flake8 (Linter)
```flake8 .```
or
```flake8 src/app/main.py```

## Export Requirements With Poetry
### First install the Plugin
```poetry self add poetry-plugin-export```
Them ...
### Generate Without Hashes
```poetry export -f requirements.txt --output requirements.txt --without-hashes```
### Generate  With Hashes
```poetry export -f requirements.txt --output requirements.txt```