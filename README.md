## TODO
- [x] 基于文件配置 `~/.mm.json`
    
    配置文件路径由环境变量`MM_HOME`指定,默认为`~/.mm.json`

- [x] `~/.mm.json` 默认情况下自动生成
    
    1. 不存在自动生成
    2. 每次启动自动以完整配置格式更新配置文件

- [x] Indicator增加初始配置决定方法
- [x] 记录桌面位置
- [ ] 依据定位动态加载
    
    如 `package.module.Foo`
    
- [ ] 用户插件架构

    - 配置文件 `~/.mm/config.json`
    - 自定义指标 `~/.mm/indicators/XXXIndicator`

- [ ] 警报功能