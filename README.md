# Logitech_Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Windows](https://img.shields.io/badge/Platform-Windows-brightgreen.svg)](https://www.microsoft.com/windows)
[![GitHub issues](https://img.shields.io/github/issues/DTer1999/Logitech_Assistant)](https://github.com/DTer1999/Logitech_Assistant/issues)

一个基于 Python 的 Logitech G HUB 辅助工具。

## 支持的游戏

<img src="resources/assets/2.ico" alt="PUBG Logo" width="16" height="16"/> 绝地求生（PUBG）

目前仅支持绝地求生（PUBG），未来可能会支持更多游戏。

## 原理
通过图像比对，对固定位置图片截图，然后与预先的模板图片进行比对，判断是何种武器、配件，判断是否开枪等，然后将识别结果生成lua代码文件。Logitech G HUB通过doFile命令获取lua代码文件，执行代码。

## 功能特性

- 自动识别游戏中的武器和配件
- 实时显示游戏状态
- 自动记录日志
- 用户友好的界面

## 系统要求

- Python 3.8 或更高版本
- Windows 10/11
- 1920x1080 或 2560x1440 分辨率

## 使用说明

1. 以管理员身份运行Logitech G HUB
2. 启动程序后，确保 PUBG 游戏窗口处于活动状态
3. 使用界面上的开关按钮启动/停止识别
4. 当按下Tab键时，程序会自动识别当前武器和配件
5. 鼠标右键开镜时，程序会识别开枪

## 常见问题

1. 如果遇到导入错误，请确保已正确安装所有依赖
2. 如果识别不准确，请检查游戏分辨率设置
3. 如果程序无响应，请检查是否有其他程序占用相关资源
4. 如果Logitech G HUB中没有PUBG的配置文件，请手动添加，并将配置文件中的地址设置为该软件的temp文件夹下的weapon.lua文件

## 开发指南

1. 安装开发依赖：
```bash
pip install -r requirements.txt
```

2. 运行测试：
```bash
pytest tests/
```

3. 代码格式化：
```bash
black src/ tests/
```

4. 类型检查：
```bash
mypy src/
```

5. 代码风格检查：
```bash
flake8 src/ tests/
```

## 项目结构

```
Logitech_Assistant/
├── setup.py          # 包安装配置
├── requirements.txt  # 项目依赖
├── README.md         # 项目说明
├── src/              # 源代码
│   ├── main.py       # 程序入口
│   ├── core/         # 核心功能
│   ├── ui/           # 界面相关
│   ├── utils/        # 工具函数
│   └── config/       # 配置文件
├── resources/        # 资源文件
├── tests/            # 测试文件
└── temp/            # 临时文件
```

## 未来计划

- 支持配置武器、配件、开枪lua脚本参数
- 支持模板截图功能
- 支持更多游戏

## 声明

1. 源码来自于群友 SenLiao 的分享，后通过Cursor软件，调用Claude3.5模型、ChatGPT4o模型、o1模型对代码功能、结构进行优化。
2. 相关源码、软件等仅供学习和交流使用。
3. 请勿用于商业用途。如进行商业用途，请自行承担相关责任。
4. 请勿用于游戏外挂等非法用途。如用于非法用途，请自行承担相关责任。

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 作者：DTer1999
- 邮箱：hshm1999@foxmail.com
- 项目主页：https://github.com/DTer1999/Logitech_Assistant