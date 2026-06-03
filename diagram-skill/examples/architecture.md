# 架构图（architecture-beta）范本 — CCTV 监控系统架构

## CCTV 监控系统三层架构

场景：闭路电视监控系统从前端采集到中心管理的三层架构图，含 5 个核心服务和 3 个逻辑分组。适用于方案文档中说明 CCTV 系统的网络拓扑和数据流向。

```mermaid
architecture-beta
    accTitle: CCTV 监控系统架构
    accDescr: 闭路电视监控系统三层架构，前端采集到中心管理
    group frontend[前端采集]
    service camera1[摄像头] in frontend
    service camera2[摄像头] in frontend
    service camera3[摄像头] in frontend

    group transport[网络传输]
    service switch[核心交换机] in transport

    group backend[中心管理]
    service nvr[NVR 存储] in backend
    service stream[流媒体服务器] in backend
    service client[监控客户端] in backend

    camera1{R} -->> switch
    camera2{R} -->> switch
    camera3{R} -->> switch
    switch -->> nvr
    switch -->> stream
    stream -->> client
```

## 节点清单

| 节点 | 类型 | 分组 | 含义 |
|------|------|------|------|
| camera1/camera2/camera3 | service | frontend | 前端摄像头（半球/枪机/球机） |
| switch | service | transport | 核心交换机，汇聚前端流量 |
| nvr | service | backend | 网络录像机，存储视频流 |
| stream | service | backend | 流媒体服务器，协议转换 + 分发 |
| client | service | backend | 监控客户端/电视墙 |

## 分组清单

| 分组 | 角色 | 包含服务 |
|------|------|---------|
| frontend | 前端采集 | 摄像头集群 |
| transport | 网络传输 | 核心交换机 |
| backend | 中心管理 | NVR + 流媒体 + 客户端 |

## 使用提示

- 架构图用 `architecture-beta` 语法（Mermaid 10.x 新特性）
- `group` 定义逻辑分区，`service in group` 把服务挂到组里
- 边方向用 `L/R/T/B`（左/右/上/下）控制箭头朝向
- 服务超过 8 个建议拆成多个子架构图
- 中文服务名直接写在 `[]` 内，不需要引号
