---
title: 雨夜横丁关卡 Demo 设计文档
date: 2026-11-23
---

<video controls playsinline preload="metadata" width="100%" src="/assets/img/rainy-night-alley/demo.mp4"></video>

## 设计概述
背景设定：胡同中的酒吧时常传来异响，且附近有少量失踪的案例，玩家作为探员需要去探索酒吧中的秘密

| 预期体验 | 调查发现机关与额外空间 → 进入地下室探索与战斗 → 击败敌人揭露阴谋                             |
| ---- | --------------------------------------------------------------- |
| 核心动作 | 调查、找路、拿钥匙、战斗                                                    |
| 空间结构 | 酒吧大厅（地表）→ 中央酿造区 → 储藏区（3/2/1F）→ 处理区（1/2F）→ 数控区（1/2F）→ 隐藏门 → 酒吧走廊 |
| 主要区域 | 酒吧大厅、中央酿造区、储藏区、处理区、数控区                                          |
| 节奏   | 调查（缓）→ 下行探索（紧）→ 取钥匙（小高潮）→ 折返（回收）→ 数控室战斗（高潮） → 回到酒吧（释放）          |
## 参考图
![581](/assets/img/rainy-night-alley/Pasted%20image%2020261120144343.png)![577](/assets/img/rainy-night-alley/Pasted%20image%2020261123203329.png)

## 实际流程
流程描述：与包间里的线人完成对话，获得线索与地下室钥匙，然后从厕所隔间进入地下室中央区，从中央二楼进入储藏区三楼，然后依次完成储藏区二楼和一楼探索，从储藏区一楼进入处理室，上到处理室二楼找到数控室钥匙，然后穿过储藏区二楼回到中央区，使用钥匙进入数控区，从数控区二楼开启隐藏门回到酒吧走廊
### 游戏节奏图
通过以下方式实现波浪式递增的游戏节奏
1穿插战斗与探索
2敌人数量与压力增加
3空间逐渐狭窄，亮暗对比增强
![](/assets/img/rainy-night-alley/Pasted%20image%2020261123204219.png)


### 流程图
![](/assets/img/rainy-night-alley/Pasted%20image%2020261123202127.png)
### 结构图
![](/assets/img/rainy-night-alley/Pasted%20image%2020261123101014.png)
### 动线演示
![](/assets/img/rainy-night-alley/Pasted%20image%2020261123101900.png)![](/assets/img/rainy-night-alley/Pasted%20image%2020261123112616.png)

## 重要节点
- 胡同用克制的冷色夜光，暖色入口和台面帮助定位。保留街边店面与连续墙面的空间关系。
![](/assets/img/rainy-night-alley/Pasted%20image%2020261123214415.png)
- 用书柜/酒柜伪装隐藏起来的暗门，玩家会从另一侧回到这个场景，隐藏出口管理预期
![](/assets/img/rainy-night-alley/Pasted%20image%2020261123214524.png)
- 初入中央区，第一眼看见敌人与收集物 ![](/assets/img/rainy-night-alley/Pasted%20image%2020261123215251.png)
- 前进发现脚底的敌人，回头发现剩余敌人
![](/assets/img/rainy-night-alley/Pasted%20image%2020261123215432.png)
![](/assets/img/rainy-night-alley/Pasted%20image%2020261123215645.png)
- 预期路线用更亮的灯光引导，另一条路线能看到较暗的障碍物
![](/assets/img/rainy-night-alley/Pasted%20image%2020261123215737.png)
- 较近处用收集物吸引注意力，远处能看到门牌但发现是锁住状态
![](/assets/img/rainy-night-alley/Pasted%20image%2020261123215943.png)
- 进门能发现明显战斗点，贴近发现额外敌人创造意外
![](/assets/img/rainy-night-alley/Pasted%20image%2020261123220151.png)
![](/assets/img/rainy-night-alley/Pasted%20image%2020261123220334.png)
- 用收集物吸引玩家深入，再回头能提前发现底层的敌人
![](/assets/img/rainy-night-alley/Pasted%20image%2020261123220557.png)
- 升降台处能发现底层的敌人，同时看见远处的收集物，与门一起建立第二目标
![](/assets/img/rainy-night-alley/Pasted%20image%2020261123224944.png)
- 利用光影塑造压迫感与紧张感
![](/assets/img/rainy-night-alley/Pasted%20image%2020261123221554.png)
## 对话、收集物配表
![](/assets/img/rainy-night-alley/Pasted%20image%2020261123194451.png)
## UE 配置索引

| 要修改的内容     | 在哪里操作                                                                                                               | 联动检查                                                                                      |
| ---------- | ------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| 灰盒空间与路标    | 原图 `Template_Default`，用 Blockout Tools 修改几何。分叉路标用 `BP_BlockAnnotation`。                                             | 地面与地下使用同一张主图。更新楼层后同步地图标注、门和触发范围。                                                          |
| 台词、选项和停留时间 | `Content/DialogueCSV/YokochoStory.csv`。用 `Id`、`Next` 串接，`Shot`、`Transition`、`Blend`、`Hold`、`Auto` 控制演出。             | `Choice` 的 `Id` 指向所属对话节点。资产的 `Start` 对应首节点。                                               |
| NPC 与镜头    | 小川、包间客人用 `BP_DialogueNPC`。在 Details 改角色名、待机与 `Shots`，镜头在 Cine Camera 或 Sequencer 调整。                                | 镜头 ID 与 CSV 一致，从每个分支退出都要检查镜头和行动恢复。                                                        |
| 大厅短句与录音    | `BP_DialoguePoint`。大厅说话点开启 `Show As Bark`，录音按原有节点可重听。                                                               | 挪动模型后检查说话点距离、朝向与台面遮挡。                                                                     |
| 证据与钥匙      | `BP_StoryNote` 或 `BP_KeyPickup`。Details 的 `Pickup Label` 管动作，`Item Name` 管取得后的名称。                                   | 工服实例需同时配置 `Key Id = Brewery.StallKey` 和 `Grants Key`，拾取正文来自 `Guest.Coat`。数控钥匙的 ID 与数控门一致。 |
| 数控门与数控台    | 门实例的 `Locked Label` 对应 `Control.Locked`。终端的 `Blocked Text` 与 `Required Defeated` 对应警戒反馈与指定值守。                       | 改表里的这两条文本时，同步 Details。数控台引用 `Terminal.Start`。                                             |
| 暗门与结尾      | 暗门实例 `BP_MechanismDoor_C_4` 的 `Open Trigger` 指向大纲中的「暗门｜打开后的结尾」。选中该触发器改 `Trigger Text`、`Trigger Text Seconds` 与退场对象。 | 暗门需要 `Brewery.FinalRecord`。两个旧靠近触发盒的碰撞都已关闭，结尾触发器由门到位事件调用。                                 |
| 机关门与升降平台   | `BP_MechanismDoor` 和 `BP_PlatformCall`。在 Details 调门板尺寸、运动方式、允许侧、旋转轴、停靠端点与到站行为。                                      | 改尺寸优先用 `Leaf Size`。平台护栏附到随门板移动的组件，两个呼叫点指向相应端点。                                            |
