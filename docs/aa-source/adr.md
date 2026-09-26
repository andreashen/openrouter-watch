# ADR：评测上游在授权前保持双轨

## 状态

已接受。公开切流未执行。

## 背景

主榜需要同一版 Intelligence Index 上的三项分数。Artificial Analysis 的 Free Data API 能提供这三项和 major.minor 版本，但 Free 档位的许可是内部使用，不是公开转载权。

## 决定

1. 机器可读源用官方 Data API。内部验证走 Free 端点。
2. 公开主榜继续读 OpenRouter 转载分，derive 的空白回填也先保留。停采必须发生在切流并且再成功刷新一次之后。
3. 映射只来自冻结文件。一对多 group 必须记录每个成员的身份依据，校验失败则整份映射无边。
4. AA 分数不跨快照补字段。

## 后果

在书面授权写进 `publication.json` 的 `g0`、并且展示开关被有意打开之前，页面数字不会变成 AA 直连值。内部快照不进入 git。
