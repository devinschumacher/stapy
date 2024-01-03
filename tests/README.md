# Tests

## Add files

```shell
cp stapy.py tests/stapy.py; \
cp -r plugins/editor tests/plugins
```

## Unit tests

```shell
python3 tests/run.py
```

## Code Analyser

```shell
pip install pylint
```

```shell
python3 -m pylint stapy.py plugins/*.py
```

## e2e tests

### Install Cypress

```shell
cd tests
npm install cypress@13.1.0 --save-dev
```

### Run tests

#### Terminal 1

```shell
python3 tests/stapy.py
```

#### Terminal 2

```shell
cd tests
npx cypress run
```