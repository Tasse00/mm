# Mini Monitor

`Configurable` `Expandable` `Draggable` `TopWindow`

![example](./doc/example.png)

## Install

```
# only tested in python3 and take care of PyQt5 environtments
pip install mini-monitor
```     

## Run

```
$ nohup mm &
```

## Configure

If `MM_HOME` env is not set, the config dir is default to `~/.mm`. 

Config file is located at `$MM_HOME/config.yaml` .

Custom Indicators & Sensors can be placed in `$MM_HOME/indicators` and `$MM_HOME/sensors` .

## Architecture

Todo ...

## Config File

Todo ... 

## UI File

Todo ...

## TODO

- [x] Settings - GUI Editing Capacity 

- [x] The Type of Indicator & Sensor in GUI Settings should be "select". 

- [ ] Multi Panel!

    Shared DataStore
    Separated Indicator Container Widget
