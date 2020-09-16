## TODO
- [x] 基于文件配置 `~/.mm.json`
    
    配置文件路径由环境变量`MM_HOME`指定,默认为`~/.mm.json`

- [x] `~/.mm.json` 默认情况下自动生成
    
    1. 不存在自动生成
    2. 每次启动自动以完整配置格式更新配置文件

- [x] Indicator增加初始配置决定方法
- [x] 记录桌面位置
- [x] 依据定位动态加载
    
    如 `package.module.Foo`
    
- [x] 用户插件架构

    - 配置文件 `~/.mm/config.json`
    - 自定义指标 `~/.mm/indicators/XXXIndicator`

- [x] 历史数据
    
    1. Sensor 与 Indicator 分离
    2. 引入 DataStore 提供存储及获取数据的能力

- [x] 除了Indicator外的 UI独立为资源文件

- [ ] GUI配置能力
- [ ] 警报功能?
- [ ] 中央插件仓库?