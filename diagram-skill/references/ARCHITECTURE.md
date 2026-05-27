# ELV System Architecture Diagrams / 弱电系统架构图集

> 注：以下图表使用 `flowchart` 语法撰写，确保与 Mermaid 10.x（Obsidian 内置版本）完全兼容。

---

## 1. 弱电系统整体架构

弱电系统整体架构分为用户层、网络层、系统层和数据层，涵盖门禁、视频监控、报警等核心子系统。

```mermaid
flowchart TD
    accTitle: 弱电系统整体架构
    accDescr: 弱电系统分为用户层、网络层、系统层和数据层，包含刷卡器、摄像头、交换机、路由器、防火墙及各服务子系统

    subgraph 用户层
        A1["[ 刷卡器 ]\n访客/员工"]:::node
        A2["[ 摄像头 ]"]:::node
    end

    subgraph 网络层
        B1["[ 接入层交换机 ]"]:::node
        B2["[ 核心路由器 ]"]:::node
        B3["[ 防火墙 ]"]:::node
    end

    subgraph 系统层
        C1["[ 门禁主机 ]"]:::node
        C2["[ 视频管理平台 ]"]:::node
        C3["[ 报警主机 ]"]:::node
    end

    subgraph 数据层
        D1["[ 业务数据库 ]"]:::node
        D2["[ NVR存储 ]"]:::node
        D3["[ 云端备份 ]"]:::node
    end

    A1 -->|"刷卡验证"| B1
    A2 -->|"视频采集"| B1
    B1 --> B2
    B1 --> B3
    B2 --> C1
    B2 --> C2
    B2 --> C3
    C1 --> D1
    C2 --> D2
    C2 --> D3

    style 用户层 fill:#e8f5e9,stroke:#4caf50
    style 网络层 fill:#e3f2fd,stroke:#2196f3
    style 系统层 fill:#fff3e0,stroke:#ff9800
    style 数据层 fill:#f3e5f5,stroke:#9c27b0

    classDef node fill:#fff,stroke:#333,stroke-width:1.5px
```

---

## 2. 智慧楼宇系统架构

智慧楼宇系统架构分为终端层、网络层、平台层和应用层，整合楼控、安防、运维等多个子系统。

```mermaid
flowchart TD
    accTitle: 智慧楼宇系统架构
    accDescr: 智慧楼宇系统从下到上分为终端层、网络层、平台层和应用层，实现从传感器到Web/APP/大屏的完整链路

    subgraph 终端层
        T1["[ 温湿度传感器 ]"]:::node
        T2["[ 监控摄像头 ]"]:::node
        T3["[ 门禁读卡器 ]"]:::node
    end

    subgraph 网络层
        N1["[ 楼层交换机 ]"]:::node
        N2["[ 汇聚交换机 ]"]:::node
        N3["[ 物联网网关 ]"]:::node
    end

    subgraph 平台层
        P1["[ BA楼宇自控平台 ]"]:::node
        P2["[ 综合安防平台 ]"]:::node
        P3["[ 运维管理平台 ]"]:::node
    end

    subgraph 应用层
        A1["[ Web管理端 ]"]:::node
        A2["[ 手机APP ]"]:::node
        A3["[ 信息发布大屏 ]"]:::node
    end

    T1 --> N1
    T2 --> N1
    T3 --> N1
    N1 --> N2
    N2 --> N3
    N3 --> P1
    N3 --> P2
    N3 --> P3
    P1 --> A1
    P2 --> A2
    P3 --> A3

    style 终端层 fill:#e8f5e9,stroke:#4caf50
    style 网络层 fill:#e3f2fd,stroke:#2196f3
    style 平台层 fill:#fff3e0,stroke:#ff9800
    style 应用层 fill:#f3e5f5,stroke:#9c27b0

    classDef node fill:#fff,stroke:#333,stroke-width:1.5px
```

---

## 3. 数据中心机房架构

数据中心机房架构分为机房基础设施、IT基础设施、网络基础设施和监控管理四大模块，保障机房安全稳定运行。

```mermaid
flowchart TD
    accTitle: 数据中心机房架构
    accDescr: 数据中心机房分为基础设施、IT设备、网络设备和监控管理四部分，包含精密空调、UPS、服务器、交换机和CCTV等

    subgraph 基础设施
        I1["[ 精密空调 ]"]:::node
        I2["[ UPS电源 ]"]:::node
        I3["[ 气体灭火 ]"]:::node
    end

    subgraph IT基础设施
        IT1["[ 计算服务器 ]"]:::node
        IT2["[ 存储阵列 ]"]:::node
        IT3["[ 虚拟化平台 ]"]:::node
    end

    subgraph 网络基础设施
        NW1["[ 核心交换机 ]"]:::node
        NW2["[ 汇聚交换机 ]"]:::node
        NW3["[ 负载均衡器 ]"]:::node
    end

    subgraph 监控管理
        M1["[ 动环监控 ]"]:::node
        M2["[ 视频监控 ]"]:::node
        M3["[ 门禁系统 ]"]:::node
    end

    I1 --> I2 --> I3
    IT1 --> IT2 --> IT3
    NW1 <-->|"万兆"| NW2
    NW2 --> NW3
    NW1 <-->|"管理"| IT基础设施
    NW1 <-->|"监控"| 监控管理

    style 基础设施 fill:#e8f5e9,stroke:#4caf50
    style IT基础设施 fill:#e3f2fd,stroke:#2196f3
    style 网络基础设施 fill:#fff3e0,stroke:#ff9800
    style 监控管理 fill:#f3e5f5,stroke:#9c27b0

    classDef node fill:#fff,stroke:#333,stroke-width:1.5px
```

---

## 4. 视频监控系统架构

视频监控系统架构分为前端采集、传输网络、后端存储和显示控制四个环节，实现从采集到显示的全链路管理。

```mermaid
flowchart LR
    accTitle: 视频监控系统架构
    accDescr: 视频监控系统从前到后分为前端采集、传输网络、后端存储和显示控制四个层级，包含摄像头、交换机、NVR和解码器等设备

    subgraph 前端采集
        F1["[ 半球摄像机 ]"]:::node
        F2["[ 高速球机 ]"]:::node
        F3["[ 热成像相机 ]"]:::node
    end

    subgraph 传输网络
        N1["[ 接入交换机 ]"]:::node
        N2["[ 光纤收发器 ]"]:::node
        N3["[ POE交换机 ]"]:::node
    end

    subgraph 后端存储
        S1["[ NVR录像机 ]"]:::node
        S2["[ IPSAN存储 ]"]:::node
        S3["[ 云存储 ]"]:::node
    end

    subgraph 显示控制
        D1["[ 视频矩阵 ]"]:::node
        D2["[ 解码器 ]"]:::node
        D3["[ 控制键盘 ]"]:::node
    end

    F1 & F2 & F3 -->|"网线/光纤"| N1
    N1 --> N2 --> N3
    N3 -->|"存储通道"| S1
    N3 -->|"备份"| S2
    N3 -->|"云端"| S3
    S1 --> D1
    S2 --> D2
    S3 --> D3

    style 前端采集 fill:#e8f5e9,stroke:#4caf50
    style 传输网络 fill:#e3f2fd,stroke:#2196f3
    style 后端存储 fill:#fff3e0,stroke:#ff9800
    style 显示控制 fill:#f3e5f5,stroke:#9c27b0

    classDef node fill:#fff,stroke:#333,stroke-width:1.5px
```

---

## 5. 会议系统架构

会议系统架构分为信号源、传输处理、显示输出和控制管理四个部分，满足现代化会议音视频需求。

```mermaid
flowchart LR
    accTitle: 会议系统架构
    accDescr: 会议系统从信号源到显示输出分为四层，包含摄像机、笔记本、矩阵、投影、音响和中控等设备

    subgraph 信号源
        S1["[ 会议摄像机 ]"]:::node
        S2["[ 笔记本电脑 ]"]:::node
        S3["[ 无线投屏器 ]"]:::node
    end

    subgraph 传输处理
        T1["[ HDMI矩阵 ]"]:::node
        T2["[ 数字音频处理器 ]"]:::node
        T3["[ 录播服务器 ]"]:::node
    end

    subgraph 显示输出
        O1["[ 激光投影机 ]"]:::node
        O2["[ LED拼接屏 ]"]:::node
        O3["[ 专业音箱 ]"]:::node
    end

    subgraph 控制管理
        C1["[ 中控主机 ]"]:::node
        C2["[ 触控面板 ]"]:::node
        C3["[ 电源时序器 ]"]:::node
    end

    S1 & S2 --> T1
    S3 --> T2
    T1 --> T2 --> T3
    T3 --> O1
    T3 --> O2
    T1 --> O3
    C1 --> C2
    C1 --> T1
    C2 --> T1

    style 信号源 fill:#e8f5e9,stroke:#4caf50
    style 传输处理 fill:#e3f2fd,stroke:#2196f3
    style 显示输出 fill:#fff3e0,stroke:#ff9800
    style 控制管理 fill:#f3e5f5,stroke:#9c27b0

    classDef node fill:#fff,stroke:#333,stroke-width:1.5px
```

---

## 6. 弱电物联网架构

弱电物联网架构分为感知层、传输层、平台层和应用层，实现设备接入、数据处理与业务应用的端到端打通。

```mermaid
flowchart TD
    accTitle: 弱电物联网架构
    accDescr: 弱电物联网从下到上分为感知层、传输层、平台层和应用层，包含各类传感器、物联网关、IoT平台和Web/APP/短信/大屏等应用

    subgraph 感知层
        P1["[ 温湿度传感器 ]"]:::node
        P2["[ 烟感探测器 ]"]:::node
        P3["[ 水浸传感器 ]"]:::node
        P4["[ 门磁开关 ]"]:::node
    end

    subgraph 传输层
        T1["[ 物联网关 ]"]:::node
        T2["[ LORA网关 ]"]:::node
        T3["[ 协议转换器 ]"]:::node
    end

    subgraph 平台层
        PL1["[ IoT平台 ]"]:::node
        PL2["[ 数据中台 ]"]:::node
        PL3["[ 告警引擎 ]"]:::node
    end

    subgraph 应用层
        A1["[ Web监管平台 ]"]:::node
        A2["[ 手机APP ]"]:::node
        A3["[ 短信通知 ]"]:::node
        A4["[ 大屏展示 ]"]:::node
    end

    P1 --> T1
    P2 --> T1
    P3 --> T2
    P4 --> T3
    T1 --> PL1
    T2 --> PL2
    T3 --> PL3
    PL1 --> A1
    PL2 --> A2
    PL3 --> A3
    PL3 --> A4

    style 感知层 fill:#e8f5e9,stroke:#4caf50
    style 传输层 fill:#e3f2fd,stroke:#2196f3
    style 平台层 fill:#fff3e0,stroke:#ff9800
    style 应用层 fill:#f3e5f5,stroke:#9c27b0

    classDef node fill:#fff,stroke:#333,stroke-width:1.5px
```

---

*编制人：DUDU&Cailleach*