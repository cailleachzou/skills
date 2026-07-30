# officecli 语义参考表（xlsx 行/列/合并/公式/close）

> 实验对象：`references/TendoCN - Cooley LLP - Cooley Shanghai Meeting Room Retrofit - Weekly Progress Report (项目周报) .xlsx`
> 实验脚本：`test/_probe_1_row.py` ~ `test/_probe_7_before_after.py`（可复现）
> 实验时间：2026-07-30
> 方法：复制模板到 test/ → 执行 officecli → `officecli close` → openpyxl 读取 → 清理
> 编制：DUDU&Cailleach

---

## 0. 速查表

| 操作 | 命令 | 真实语义 | 关键陷阱 |
|------|------|----------|----------|
| 插入行 | `add <f> /Sheet --type row --index N` | **N 是 0-based**，新行落在 row(N+1) | 与 col 不对称；想插入到 row K 前用 `--index K-1` |
| 插入列 | `add <f> /Sheet --type col --index N` | **N 是 1-based**，新列落在 col N | `--index 0` 破坏文件；字母报错 |
| 插入列（推荐） | `add <f> /Sheet --type col --prop name=X` | 在 X 列**前**插入 | — |
| 插入行/列（最推荐） | `--before /Sheet/row[K]` / `--after /Sheet/row[K]` | 语义直观 | 无 |
| 删行 | `remove <f> /Sheet/row[N]` | N 是 1-based；下方合并区上移 | 被删行的合并区随之删除 |
| 删列 | `remove <f> /Sheet/col[X]` | X 是字母；引用该列的公式变 `#REF!` | 删列后必须重写公式 |
| 合并 | `set <f> /Sheet/A1 --prop merge=A1:C3` | A1 必须是 range 左上角 | **不能直接扩展已有合并区**，先 `merge=false` |
| 解除合并 | `set <f> /Sheet/A1 --prop merge=false` | 锚单元格值保留 | — |
| 外部读取前 | `officecli close "<f>"` | flush + 释放锁 | 不 close 则 openpyxl 读不到（需等 2-10s auto-flush） |

---

## 1. add row --index N 的真实插入位置

### 结论
**`--index N` 是 0-based**。新行落在 1-based 的 **row(N+1)**，原 row(N+1) 及之后全部下移 1 行。officecli 自身输出可验证：`--index 14` → `Added row at /Progress Report/row[15]`。

- 想在 row K **前**插入 → `--index K-1`
- 想在 row K **后**插入 → `--index K`
- **推荐改用 `--before /Sheet/row[K]` / `--after /Sheet/row[K]`，避免 0-based 心算**（见 §7）

### 证据（模板标记 B17='Reception and large conference room'）

| 命令 | officecli 输出 | B17 原='Reception' 新位置 | 说明 |
|------|----------------|---------------------------|------|
| `--index 14` | `row[15]` | → row 18 | 0-based 14 = 1-based 15；原 row15+ 下移，Reception 17→18 |
| `--index 17` | `row[18]` | 留在 row 17（新空行在 18） | 0-based 17 = 1-based 18 |
| `--index 20` | `row[21]` | 留在 row 17 | 0-based 20 = 1-based 21 |
| `--index 0`  | `row[1]`  | → row 18 | 0-based 0 = 1-based 1 |
| `--index 1`  | `row[2]`  | → row 18 | 0-based 1 = 1-based 2 |

公式与合并区跟随行位移自动调整（Reception 行的 `=AVERAGE(C17,F17,I17,L17,O17,R17,U17)` 移到 X18，引用同步更新为 `C18,F18,...`）。

---

## 2. add col --index 的真实语义

### 结论
- `--index` **只接受整数**，传字母直接报错：`Cannot parse argument 'X' for option '--index' as expected type 'System.Nullable\`1[System.Int32]'`
- col 的 `--index N` 是 **1-based**（与 row 的 0-based 不对称！）：N=1→A, N=2→B, N=3→C, N=24→X。新列落在 col N，原 col N 及之后右移 1。
- **`--index 0` 破坏性**：生成 `min=0` 的无效列定义，openpyxl 读取报 `ValueError: Invalid column index 0`，文件损坏。
- 想在 col K **前**插入 → `--index K`（1-based）
- 想在 col K **后**插入 → `--index K+1`
- **推荐改用 `--prop name=<字母>` 或 `--before/--after`**（见 §7）

### 证据（模板标记 X13='Overall Percentage'，C13='Demolition'）

| 命令 | officecli 输出 | 'Demolition'(原C) 新位置 | 'Overall'(原X) 新位置 | 说明 |
|------|----------------|--------------------------|-----------------------|------|
| `--index X` | **报错** | — | — | 字母无法解析为 Int32 |
| `--index C` | **报错** | — | — | 同上 |
| `--index 0` | `col[]`（空） | — | — | **文件损坏**，openpyxl 无法读 |
| `--index 1` | `col[A]` | C→D | X→Y | 1-based：N=1→A |
| `--index 2` | `col[B]` | C→D | X→Y | 1-based：N=2→B |
| `--index 3` | `col[C]` | C→D | X→Y | 1-based：N=3→C |
| `--index 24` | `col[X]` | 留在 C | X→Y | 1-based：N=24→X |
| `--prop name=X` | `col[X]` | 留在 C | X→Y | 在 X 前插入，公式 `=AVERAGE(C17,F17,I17,L17,O17,R17,U17)` 不变（X 在引用列之后） |

`--prop name=X` 与 `--index 24` 效果相同，但语义更清晰。

---

## 3. remove row[N] 对合并区的影响

### 结论
- `remove /Sheet/row[N]`，N 是 **1-based**。
- 被删行自身携带的合并区（如该行是某合并区的一部分）随之删除。
- 下方所有合并区**整体上移**，**行跨度与列范围保持不变**。
- 与官方文档"mergeCells follows the displacement"一致。

### 证据（Issue_RFA Log，合并区 A18:C19='RFI / RFA LOG'，C14:D14~C17:D17 是 4 个 Issue 描述合并）

**删 row[14] 1 次：**
| 合并区 | 前 | 后 |
|--------|----|----|
| A18:C19（RFA title） | A18:C19 | **A17:C18**（上移1，跨度2行×3列不变） |
| C14:D14（Issue1） | C14:D14 | **删除**（随 row14 删除） |
| C15:D15（Issue2） | C15:D15 | C14:D14（上移1） |
| C16:D16（Issue3） | C16:D16 | C15:D15 |
| C17:D17（Issue4） | C17:D17 | C16:D16 |
| A9:C10 | A9:C10 | A9:C10（不动，在删除行上方） |

'RFI / RFA LOG' 文本从 A18 → A17。

**删 row[14] 4 次（依次删掉 4 个 Issue）：**
- A18:C19 → **A14:C15**（上移4）
- 4 个 C:D 小合并区全部删除
- 'RFI / RFA LOG' 从 A18 → A14

---

## 4. remove col[字母] 对公式的影响

### 结论
- `remove /Sheet/col[X]`，X 是**列字母**（`col[数字]` 不支持，`col[字母]` 支持）。
- **引用被删列的公式 → `#REF!`**（确认用户之前的观察）。
- 未被删列的引用**自动按位移调整**（如删 O 列后，原 R 列引用→Q 列）。
- 合并区、`AVERAGE(range)` 这类区间引用自动跟随位移。
- **删列后必须重写所有引用该列的公式**（把 `#REF!` 替换或重新构造引用），否则公式返回 `#REF!` 错误。

### 证据（模板 X17=`=AVERAGE(C17,F17,I17,L17,O17,R17,U17)`，X23=`=AVERAGE(X15:X22)`）

**删 col[O] 1 次（O 是第5阶段 Testing 首列）：**
- X17 → **W17**（X 左移到 W），公式变为：
  `=AVERAGE(C17,F17,I17,L17,#REF!,Q17,T17)`
  - O17 → `#REF!`（被删）
  - R17 → Q17（R 左移到 Q）
  - U17 → T17（U 左移到 T）
  - C17/F17/I17/L17 不变（在 O 左侧）
- 合并区：O13:Q13(Testing) 删除；R13:T13(Labelling)→Q13:S13；U13:W13(System)→T13:V13；C12:W12→C12:V12
- X23=`=AVERAGE(X15:X22)` → W23=`=AVERAGE(W15:W22)`（自动调整）

**删 col[O] 3 次（删掉整个 O-Q 阶段块）：**
- X17 → **U17**（左移3列），公式变为：
  `=AVERAGE(C17,F17,I17,L17,#REF!,O17,R17)`
  - O17 → `#REF!`（公式只引用 O17，未引用 P/Q，故仅 1 个 #REF!）
  - 原 R17 → O17，原 U17 → R17
- 合并区：O13:Q13(Testing) 整块删除；R13:T13→O13:Q13；U13:W13→R13:T13

---

## 5. set --prop merge 的用法与限制

### 结论
- `set <f> /Sheet/A1 --prop merge=A1:C3`：创建合并区，**A1 必须是 range 的左上角锚单元格**。
- 空区域、相邻不重叠区域：成功。
- **幂等**：对已有合并区重设相同范围，成功且无变化。
- **不能直接扩展/缩小已有合并区**：与现有合并区重叠时报错 `Merge range '...' overlaps existing merged range '...'. Excel rejects overlapping mergeCell entries.`。必须先 `merge=false` 解除，再设新范围。
- `set <f> /Sheet/A1 --prop merge=false`（别名 `unmerge`/`none`/`empty`）：解除合并，**锚单元格值保留**，其余单元格清空。
- `add <f> /Sheet --type cell --prop ref=Z20 --prop merge=Z20:Z22`：创建单元格同时合并。
- merge 可跨多行多列，可逗号分隔多个 range：`merge=A1:B1,A2:B2`。

### 证据

| 测试 | 命令 | 结果 |
|------|------|------|
| 5a 空区域单列多行 | `set /Progress Report/Z10 --prop merge=Z10:Z15` | ✓ 新增 Z10:Z15 |
| 5b 空区域多列多行 | `set /Progress Report/Z10 --prop merge=Z10:AA12` | ✓ 新增 Z10:AA12 |
| 5c 幂等重设 | `set /Progress Report/C13 --prop merge=C13:E13`（C13:E13 已存在） | ✓ 无变化 |
| 5d **扩展已有合并区** | `set /Progress Report/C13 --prop merge=C13:F13`（原 C13:E13） | ✗ 报错 overlaps |
| 5e 解除合并 | `set /Progress Report/C13 --prop merge=false` | ✓ C13:E13 消失，C13='Demolition' 保留 |
| 5f 相邻不重叠（下方有数据） | `set /Progress Report/C14 --prop merge=C14:E14`（C13:E13 正下方，C14='%'） | ✓ 新增 C14:E14，C14='%' 保留 |
| 5g add cell + merge | `add /Progress Report --type cell --prop ref=Z20 --prop merge=Z20:Z22` | ✓ 新增 Z20:Z22 |

**扩展合并区的正确流程**（如 C13:E13 → C13:F13）：
```powershell
officecli set "<f>" "/Progress Report/C13" --prop merge=false
officecli set "<f>" "/Progress Report/C13" --prop merge=C13:F13
```

---

## 6. open/close 机制

### 结论
- **`set`/`add`/`remove` 等写命令即使不显式 `open`，也会启动常驻进程**（resident）。命令返回时修改在内存，**未刷盘**。
- **外部程序（openpyxl / Excel / 任何非 officecli 进程）读取前必须 `close` 或 `save`**，否则读不到修改（需等 2-10s auto-flush）。
- `close <f>` = flush 到磁盘 + 停止常驻（释放文件锁）。
- `save <f>` = flush 到磁盘 + 保持常驻（后续命令仍快）。
- officecli 自身的 `get`/`query` 读操作总能看到最新修改（不需 flush）。
- **agent 指令铁律：每次 officecli 写操作后、且需要外部读取（openpyxl 验证/Excel 打开）前，必须 `officecli close "<f>"`。**

### 证据（写 Z1=1, Z2=2, Z3=3 到 Progress Report，然后 openpyxl 读）

| 场景 | 立即读 | 等 1s | 等 12s | close 后读 |
|------|--------|-------|--------|-----------|
| 6a 不 open，3 次 set，不 close | Z=None ❌ | Z=None ❌ | — | — |
| 6b open，3 次 set，不 close | Z=None ❌ | Z=None ❌ | — | — |
| 6c open，3 次 set，**close** | — | — | — | Z=1,2,3 ✓ |
| 6d open，3 次 set，不 close，等 12s | — | — | Z=1,2,3 ✓（auto-flush） | — |
| 6e 不 open，单次 set，不 close | Z=None ❌ | — | — | — |

6a/6e 的 `close` 输出 `Resident closed for ...` 证实：即便没显式 `open`，set 也启动了常驻。6c 第二次 close 输出 `already saved to disk; nothing to close` 证实 close 后常驻已停止。

---

## 7. 补充：--before / --after（推荐替代 --index）

### 结论
`--before` / `--after` 接受 element path，语义直观无歧义，**强烈推荐用于替代 `--index`**，避开 row 0-based / col 1-based 的不对称陷阱。

| 命令 | 含义 |
|------|------|
| `add <f> /Sheet --type row --before /Sheet/row[K]` | 在 row K **前**插入新行 |
| `add <f> /Sheet --type row --after /Sheet/row[K]` | 在 row K **后**插入新行 |
| `add <f> /Sheet --type col --before /Sheet/col[X]` | 在 col X **前**插入新列 |
| `add <f> /Sheet --type col --after /Sheet/col[X]` | 在 col X **后**插入新列 |

### 证据

| 命令 | officecli 输出 | 'Reception'(原17)/'Overall'(原X) 新位置 |
|------|----------------|----------------------------------------|
| `--after /Progress Report/row[16]` | `row[17]` | Reception 17→18（新行在 17） |
| `--before /Progress Report/row[17]` | `row[17]` | Reception 17→18（新行在 17） |
| `--before /Progress Report/col[X]` | `col[X]` | Overall X→Y（新列在 X） |
| `--after /Progress Report/col[W]` | `col[X]` | Overall X→Y（新列在 X） |

`--after row[16]` 与 `--before row[17]` 等价；`--before col[X]` 与 `--after col[W]` 等价。

---

## 8. agent 指令设计建议

### 推荐用法
1. **插入行/列**：用 `--before` / `--after`，不要用 `--index`。
   ```powershell
   # 在 row 17（Reception 行）前插入新行
   officecli add "<f>" "/Progress Report" --type row --before "/Progress Report/row[17]"
   # 在 X 列（Overall）前插入新列
   officecli add "<f>" "/Progress Report" --type col --before "/Progress Report/col[X]"
   ```
2. **删除行/列**：`remove /Sheet/row[N]`（1-based）/ `remove /Sheet/col[X]`（字母）。
3. **合并区扩展/调整**：先 `merge=false` 解除，再设新 `merge=<range>`。
4. **每次写操作后**：`officecli close "<f>"` 释放锁，再用 openpyxl 验证。

### 禁止/高风险用法
- ❌ `add col --index 0`：破坏文件（生成 min=0 无效列）。
- ❌ `add col --index <字母>`：直接报错。
- ❌ `add row --index N` 当 1-based 用：实际插入到 row(N+1)，错位。
- ❌ 直接 `set A1 --prop merge=<更大的范围>` 扩展已有合并区：报错 overlaps。
- ❌ 删列后不重写公式：引用该列的公式变 `#REF!`，整个公式返回错误。
- ❌ 写操作后不 `close` 就用 openpyxl 读：读不到修改（除非等 2-10s）。

### 删列后重写公式的标准流程
```powershell
# 假设要删 col[O]（Testing 阶段首列），X17 原公式 =AVERAGE(C17,F17,I17,L17,O17,R17,U17)
officecli remove "<f>" "/Progress Report/col[O]"
officecli close "<f>"
# 此时原 X17 已左移到 W17，公式变 =AVERAGE(C17,F17,I17,L17,#REF!,Q17,T17)
# 重写：去掉 #REF!，重新构造 6 阶段平均
officecli set "<f>" "/Progress Report/W17" --prop formula="AVERAGE(C17,F17,I17,L17,Q17,T17)"
officecli close "<f>"
```

---

## 附录：实验脚本清单

| 脚本 | 探测点 |
|------|--------|
| `test/_probe_lib.py` | 公共库（copy_template / run_oci / safe_load / cleanup） |
| `test/_probe_inspect.py` | 模板结构勘察 |
| `test/_probe_1_row.py` | add row --index 14/17/20 |
| `test/_probe_2_col.py` | add col --index X/C, name=X, --index 3, --shift right |
| `test/_probe_2b_col_idx.py` | add col --index 1/2/3/24, add row --index 0/1 |
| `test/_probe_3_rmrow_merge.py` | remove row[14] ×1/×4 对合并区影响 |
| `test/_probe_4_rmcol_formula.py` | remove col[O] ×1/×3 对公式影响 |
| `test/_probe_5_merge.py` | set --prop merge 7 种场景 |
| `test/_probe_6_close.py` | open/close 机制 5 种场景 |
| `test/_probe_7_before_after.py` | --before/--after 4 种场景 |
