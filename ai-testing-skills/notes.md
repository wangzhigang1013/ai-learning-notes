# AI 算法能力测评 — 自定义 Skill 设计方案

> 调研日期：2026-06-25
> 核心结论：现有 Skill 不适用于 AI 算法测评，建议自建 Skill

---

## 一、为什么需要自建 Skill？

### 1.1 现有 Skill 的不足

| 现有 Skill | 适用场景 | 不适用你的场景 |
|-----------|---------|--------------|
| QASkills Test Plan | 软件测试方案 | ❌ 不懂 ASR/情感/场景测评 |
| QASkills Bug Report | 软件 Bug 报告 | ❌ 不懂算法指标 |
| DeepEval | LLM 评测 | ❌ 不懂语音/音频测评 |
| Promptfoo | Prompt 测试 | ❌ 不懂收音/延迟测评 |

### 1.2 自建 Skill 的优势

- **完全匹配你的测评流程**（工牌收音 → ASR → 情感 → 场景 → 报告）
- **内置你的指标体系**（WER、CER、PESQ、STOI、准确率、召回率、F1）
- **复用测评报告模板**（每次测评自动生成标准化报告）
- **团队共享**（项目级 Skill，团队所有人可用）

---

## 二、Claude Code Skill 基础知识

### 2.1 Skill 文件结构

```
~/.claude/skills/                    # 个人级 Skill（所有项目可用）
.claude/skills/                      # 项目级 Skill（仅当前项目可用）

my-skill/
├── SKILL.md           # 主指令（必须）
├── template.md        # 报告模板（可选）
├── examples/
│   └── sample.md      # 示例输出（可选）
└── scripts/
    └── validate.sh    # 验证脚本（可选）
```

### 2.2 SKILL.md 格式

```yaml
---
name: skill-name
description: 描述这个 Skill 做什么，Claude 根据这个决定何时自动加载
when_to_use: 额外的触发条件说明
disable-model-invocation: true   # true = 只能手动 /name 调用
allowed-tools: Read Grep Bash    # 允许使用的工具
---

## 指令内容

这里写 Claude 要执行的具体步骤...
```

### 2.3 动态上下文注入

```yaml
## 当前测试数据
!`cat test-results.json`

## 当前目录结构
!`find . -name "*.wav" -type f`
```

`!` 命令会在 Skill 加载时自动执行，将结果注入到上下文中。

---

## 三、为你设计的 Skill 方案

### 3.1 Skill 一：AI 算法测评方案生成器

**用途**：根据测评需求，自动生成完整的测评方案

**文件**：`.claude/skills/ai-eval-plan/SKILL.md`

```yaml
---
name: ai-eval-plan
description: 生成 AI 算法能力测评方案。当用户需要编写 ASR 识别、情感识别、场景识别、标签识别等算法测评方案时使用。
when_to_use: 用户提到"测评方案"、"测试方案"、"算法评测"、"ASR 测试"、"情感测试"等关键词时
disable-model-invocation: true
---

## 你的角色

你是一名专业的 AI 算法测评工程师，擅长编写各类 AI 算法的测评方案。

## 测评维度

根据用户需求，从以下维度中选择需要测评的内容：

### 1. 收音质量测评
- 测评指标：信噪比（SNR）、PESQ、STOI
- 测评方法：播放标准音频，录制后对比
- 达标标准：SNR > 20dB, PESQ > 3.5, STOI > 0.9

### 2. ASR 识别准确率测评
- 测评指标：WER（词错率）、CER（字错率）
- 测评数据集：安静环境、噪声环境、方言口音、多人对话
- 达标标准：WER < 15%, CER < 10%

### 3. 语音延迟测评
- 测评指标：首字延迟、端到端延迟
- 测评方法：从说话开始到识别结果返回的时间
- 达标标准：首字延迟 < 500ms, 端到端延迟 < 2s

### 4. 情感识别测评
- 测评指标：准确率、召回率、F1
- 情感类别：Happy、Sad、Angry、Neutral、Fearful、Disgusted、Surprised
- 测评方法：标注数据集 + 混淆矩阵分析
- 达标标准：F1 > 0.8

### 5. 场景识别测评
- 测评指标：准确率、召回率、F1
- 场景类别：办公室、会议室、户外、工厂、商场等
- 测评方法：多场景录音 + 分类评估
- 达标标准：F1 > 0.85

### 6. 标签识别测评
- 测评指标：准确率、召回率、F1
- 标签类型：根据业务定义
- 测评方法：标注数据集 + 逐标签分析
- 达标标准：F1 > 0.8

### 7. 结论可靠性测评
- 测评指标：事实性结论准确率、推理性结论准确率
- 测评方法：人工标注 + AI 交叉验证
- 达标标准：准确率 > 0.9

### 8. 过程正确性测评
- 测评指标：流程合规率、异常处理率
- 测评方法：流程日志分析
- 达标标准：合规率 > 0.95

## 输出格式

生成的测评方案包含以下部分：

1. **测评概述**：背景、目的、范围
2. **测评环境**：硬件设备、软件环境、网络条件
3. **测评数据集**：数据来源、数据量、标注方法
4. **测评维度与指标**：每个维度的详细指标定义
5. **测评方法**：具体的测试步骤和流程
6. **达标标准**：每个指标的合格阈值
7. **测评排期**：时间安排和里程碑
8. **风险评估**：可能的风险和缓解措施
9. **交付物清单**：测评报告、数据集、脚本等

## 用户输入

$ARGUMENTS

请根据用户的需求，生成完整的测评方案。如果用户没有指定某些维度，主动询问是否需要包含。
```

---

### 3.2 Skill 二：AI 算法测评报告生成器

**用途**：根据测评数据，自动生成测评报告

**文件**：`.claude/skills/ai-eval-report/SKILL.md`

```yaml
---
name: ai-eval-report
description: 生成 AI 算法能力测评报告。当用户需要编写 ASR 识别、情感识别、场景识别等算法测评报告时使用。
when_to_use: 用户提到"测评报告"、"测试报告"、"评测报告"、"算法报告"等关键词时
disable-model-invocation: true
---

## 你的角色

你是一名专业的 AI 算法测评工程师，擅长编写各类 AI 算法的测评报告。

## 报告模板

请根据用户提供的测评数据，生成以下格式的测评报告：

---

# AI 算法能力测评报告

## 1. 测评概述

| 项目 | 内容 |
|------|------|
| 测评日期 | {日期} |
| 测评人员 | {人员} |
| 测评设备 | {设备} |
| 测评环境 | {环境} |
| 算法版本 | {版本} |

## 2. 测评结果汇总

| 测评维度 | 指标 | 结果 | 达标 | 备注 |
|---------|------|------|------|------|
| 收音质量 | PESQ | {值} | ✅/❌ | |
| 收音质量 | STOI | {值} | ✅/❌ | |
| ASR 识别 | WER | {值}% | ✅/❌ | |
| ASR 识别 | CER | {值}% | ✅/❌ | |
| 语音延迟 | 首字延迟 | {值}ms | ✅/❌ | |
| 语音延迟 | 端到端延迟 | {值}ms | ✅/❌ | |
| 情感识别 | F1 | {值} | ✅/❌ | |
| 场景识别 | F1 | {值} | ✅/❌ | |
| 标签识别 | F1 | {值} | ✅/❌ | |
| 结论可靠性 | 准确率 | {值}% | ✅/❌ | |
| 过程正确性 | 合规率 | {值}% | ✅/❌ | |

## 3. 详细测评结果

### 3.1 收音质量测评

| 测试项 | 测试条件 | 结果 | 达标 |
|--------|---------|------|------|
| PESQ | 安静环境 | {值} | ✅/❌ |
| PESQ | 噪声环境 | {值} | ✅/❌ |
| STOI | 安静环境 | {值} | ✅/❌ |
| STOI | 噪声环境 | {值} | ✅/❌ |

### 3.2 ASR 识别准确率

| 测试集 | WER | CER | 达标 |
|--------|-----|-----|------|
| 安静环境 | {值}% | {值}% | ✅/❌ |
| 噪声环境 | {值}% | {值}% | ✅/❌ |
| 方言口音 | {值}% | {值}% | ✅/❌ |
| 多人对话 | {值}% | {值}% | ✅/❌ |

**混淆分析**：
{列出主要的识别错误类型和示例}

### 3.3 语音延迟

| 测试项 | 平均延迟 | P95 延迟 | 达标 |
|--------|---------|---------|------|
| 首字延迟 | {值}ms | {值}ms | ✅/❌ |
| 端到端延迟 | {值}ms | {值}ms | ✅/❌ |

### 3.4 情感识别

| 情感类别 | 准确率 | 召回率 | F1 | 样本数 |
|---------|--------|--------|-----|--------|
| Happy | {值}% | {值}% | {值} | {数} |
| Sad | {值}% | {值}% | {值} | {数} |
| Angry | {值}% | {值}% | {值} | {数} |
| Neutral | {值}% | {值}% | {值} | {数} |
| Fearful | {值}% | {值}% | {值} | {数} |
| Disgusted | {值}% | {值}% | {值} | {数} |
| Surprised | {值}% | {值}% | {值} | {数} |
| **平均** | {值}% | {值}% | {值} | {数} |

**混淆矩阵**：
{列出情感之间的混淆情况}

### 3.5 场景识别

| 场景类别 | 准确率 | 召回率 | F1 | 样本数 |
|---------|--------|--------|-----|--------|
| 办公室 | {值}% | {值}% | {值} | {数} |
| 会议室 | {值}% | {值}% | {值} | {数} |
| 户外 | {值}% | {值}% | {值} | {数} |
| **平均** | {值}% | {值}% | {值} | {数} |

### 3.6 标签识别

| 标签类型 | 准确率 | 召回率 | F1 | 样本数 |
|---------|--------|--------|-----|--------|
| {标签1} | {值}% | {值}% | {值} | {数} |
| {标签2} | {值}% | {值}% | {值} | {数} |
| **平均** | {值}% | {值}% | {值} | {数} |

### 3.7 结论可靠性

| 测试项 | 准确率 | 一致性 | 达标 |
|--------|--------|--------|------|
| 事实性结论 | {值}% | {值}% | ✅/❌ |
| 推理性结论 | {值}% | {值}% | ✅/❌ |

### 3.8 过程正确性

| 测试项 | 合规率 | 达标 |
|--------|--------|------|
| 流程执行 | {值}% | ✅/❌ |
| 异常处理 | {值}% | ✅/❌ |

## 4. 问题与建议

### 4.1 主要问题
{列出测评中发现的主要问题}

### 4.2 改进建议
{针对每个问题给出具体改进建议}

## 5. 测评结论

{总体评价，是否通过测评}

## 6. 附录

- 测试数据集详情
- 测试脚本
- 详细测试结果
- 原始数据

---

## 用户输入

$ARGUMENTS

请根据用户提供的测评数据，填写上述模板，生成完整的测评报告。如果用户没有提供某些数据，主动询问。
```

---

### 3.3 Skill 三：ASR 评测执行器

**用途**：自动执行 ASR 评测，计算 WER/CER

**文件**：`.claude/skills/asr-eval/SKILL.md`

```yaml
---
name: asr-eval
description: 执行 ASR 识别准确率评测，计算 WER 和 CER。当用户需要评测 ASR 模型准确率时使用。
when_to_use: 用户提到"ASR 评测"、"WER 计算"、"CER 计算"、"语音识别准确率"等关键词时
disable-model-invocation: true
allowed-tools: Read Write Bash Grep
---

## 你的角色

你是一名专业的 ASR 评测工程师，擅长执行语音识别准确率评测。

## 评测流程

### 1. 检查测试数据

检查用户提供的测试数据格式：
- 参考文本（reference）文件：每行格式为 `utterance_id \t text`
- 识别结果（hypothesis）文件：每行格式为 `utterance_id \t text`

!`ls -la *.txt *.csv 2>/dev/null || echo "未找到测试数据文件"`

### 2. 安装评测工具

```bash
pip install jiwer
```

### 3. 执行评测

使用 Python 计算 WER 和 CER：

```python
import jiwer
import json

# 读取参考文本和识别结果
def load_data(ref_file, hyp_file):
    refs = {}
    hyps = {}
    
    with open(ref_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) == 2:
                refs[parts[0]] = parts[1]
    
    with open(hyp_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) == 2:
                hyps[parts[0]] = parts[1]
    
    return refs, hyps

# 计算指标
def calculate_metrics(refs, hyps):
    # 匹配 utterance_id
    common_ids = set(refs.keys()) & set(hyps.keys())
    
    ref_texts = [refs[uid] for uid in common_ids]
    hyp_texts = [hyps[uid] for uid in common_ids]
    
    wer = jiwer.wer(ref_texts, hyp_texts)
    cer = jiwer.cer(ref_texts, hyp_texts)
    
    return {
        'wer': wer,
        'cer': cer,
        'total_utterances': len(common_ids),
        'missing_in_hyp': len(set(refs.keys()) - set(hyps.keys())),
        'extra_in_hyp': len(set(hyps.keys()) - set(refs.keys()))
    }

# 主程序
refs, hyps = load_data('reference.txt', 'hypothesis.txt')
results = calculate_metrics(refs, hyps)

print(json.dumps(results, indent=2, ensure_ascii=False))
```

### 4. 生成报告

将评测结果整理为报告格式，包含：
- 总体 WER 和 CER
- 按说话人/场景分解的指标
- 主要错误类型分析

### 5. 错误分析

分析识别错误的类型：
- 替换错误（Substitution）
- 删除错误（Deletion）
- 插入错误（Insertion）

列出最常见的错误对。

## 用户输入

$ARGUMENTS

请根据用户提供的测试数据，执行 ASR 评测并生成报告。
```

---

### 3.4 Skill 四：情感识别评测执行器

**用途**：自动执行情感识别评测

**文件**：`.claude/skills/emotion-eval/SKILL.md`

```yaml
---
name: emotion-eval
description: 执行情感识别评测，计算准确率、召回率、F1。当用户需要评测情感识别模型时使用。
when_to_use: 用户提到"情感评测"、"情感识别准确率"、"情感 F1"等关键词时
disable-model-invocation: true
allowed-tools: Read Write Bash Grep
---

## 你的角色

你是一名专业的 AI 算法评测工程师，擅长执行情感识别评测。

## 评测流程

### 1. 检查测试数据

检查用户提供的测试数据格式：
- 标注数据文件：每行格式为 `audio_file \t true_label`
- 预测结果文件：每行格式为 `audio_file \t predicted_label`

!`ls -la *.txt *.csv 2>/dev/null || echo "未找到测试数据文件"`

### 2. 执行评测

使用 Python 计算各项指标：

```python
import json
from collections import defaultdict

def load_data(annotation_file, prediction_file):
    annotations = {}
    predictions = {}
    
    with open(annotation_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) == 2:
                annotations[parts[0]] = parts[1]
    
    with open(prediction_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) == 2:
                predictions[parts[0]] = parts[1]
    
    return annotations, predictions

def calculate_metrics(annotations, predictions):
    # 匹配文件名
    common_files = set(annotations.keys()) & set(predictions.keys())
    
    # 统计混淆矩阵
    labels = sorted(set(annotations.values()) | set(predictions.values()))
    confusion = defaultdict(lambda: defaultdict(int))
    
    for f in common_files:
        true_label = annotations[f]
        pred_label = predictions[f]
        confusion[true_label][pred_label] += 1
    
    # 计算每个类别的指标
    results = {}
    for label in labels:
        tp = confusion[label][label]
        fp = sum(confusion[other][label] for other in labels if other != label)
        fn = sum(confusion[label][other] for other in labels if other != label)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        results[label] = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'support': sum(confusion[label].values())
        }
    
    # 计算总体指标
    total_correct = sum(confusion[label][label] for label in labels)
    total_samples = len(common_files)
    accuracy = total_correct / total_samples if total_samples > 0 else 0
    
    return {
        'accuracy': accuracy,
        'per_class': results,
        'confusion_matrix': dict(confusion),
        'total_samples': total_samples
    }

# 主程序
annotations, predictions = load_data('annotations.txt', 'predictions.txt')
results = calculate_metrics(annotations, predictions)

print(json.dumps(results, indent=2, ensure_ascii=False))
```

### 3. 生成报告

将评测结果整理为报告格式，包含：
- 总体准确率
- 每个情感类别的 Precision、Recall、F1
- 混淆矩阵分析
- 主要混淆对分析

## 用户输入

$ARGUMENTS

请根据用户提供的测试数据，执行情感识别评测并生成报告。
```

---

## 四、Skill 安装与使用

### 4.1 安装方式

```bash
# 创建 Skill 目录
mkdir -p ~/.claude/skills/ai-eval-plan
mkdir -p ~/.claude/skills/ai-eval-report
mkdir -p ~/.claude/skills/asr-eval
mkdir -p ~/.claude/skills/emotion-eval

# 将 SKILL.md 文件放入对应目录
# （将上面的内容保存为对应的 SKILL.md 文件）
```

### 4.2 使用方式

```bash
# 在 Claude Code 中

# 生成测评方案
> /ai-eval-plan ASR 识别 + 情感识别 + 场景识别

# 生成测评报告
> /ai-eval-report （然后提供测评数据）

# 执行 ASR 评测
> /asr-eval reference.txt hypothesis.txt

# 执行情感识别评测
> /emotion-eval annotations.txt predictions.txt
```

### 4.3 项目级 vs 个人级

| 级别 | 路径 | 适用场景 |
|------|------|---------|
| 个人级 | `~/.claude/skills/` | 你个人所有项目可用 |
| 项目级 | `.claude/skills/` | 仅当前项目可用，可团队共享 |

**建议**：
- 通用的测评方案/报告 Skill → 个人级
- 特定项目的测评 Skill → 项目级

---

## 五、扩展建议

### 5.1 可以继续添加的 Skill

| Skill | 用途 |
|-------|------|
| `audio-quality-eval` | 收音质量评测（PESQ、STOI） |
| `latency-eval` | 语音延迟评测 |
| `scene-eval` | 场景识别评测 |
| `tag-eval` | 标签识别评测 |
| `eval-dashboard` | 生成评测可视化图表 |

### 5.2 配套脚本

可以在 Skill 目录中添加配套脚本：

```
ai-eval-plan/
├── SKILL.md
├── scripts/
│   ├── calculate_wer.py      # WER 计算脚本
│   ├── calculate_metrics.py  # 通用指标计算
│   └── generate_charts.py    # 图表生成
└── templates/
    ├── test_plan_template.md  # 测评方案模板
    └── test_report_template.md # 测评报告模板
```

### 5.3 团队共享

将 Skill 放在项目的 `.claude/skills/` 目录下，提交到 Git，团队所有人即可使用：

```bash
# 项目根目录
mkdir -p .claude/skills/ai-eval-plan
# 将 SKILL.md 放入
git add .claude/skills/
git commit -m "添加 AI 测评 Skill"
```

---

## 六、参考资料

| 资源 | 链接 |
|------|------|
| Claude Code Skills 文档 | https://code.claude.com/docs/en/skills |
| Agent Skills 标准 | https://agentskills.io |
| jiwer（WER/CER 计算） | https://github.com/jitsi/jiwer |
| FunASR（ASR 评测） | https://github.com/modelscope/FunASR |
| SenseVoice（情感识别） | https://github.com/FunAudioLLM/SenseVoice |
