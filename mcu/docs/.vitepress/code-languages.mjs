// 本站两类工具链语法的最小 TextMate 规则；不依赖把未知语言静默当 txt。
export const codeLanguages = [
  {
    name: 'ld', scopeName: 'source.ld', aliases: ['linker-script'],
    patterns: [
      { name: 'comment.block.ld', begin: '/\\*', end: '\\*/' },
      { name: 'comment.line.ld', match: '#.*$' },
      { name: 'string.quoted.double.ld', begin: '"', end: '"' },
      { name: 'constant.numeric.ld', match: '\\b(?:0[xX][0-9a-fA-F]+|[0-9]+[KkMm]?)\\b' },
      { name: 'keyword.control.ld', match: '\\b(?:MEMORY|SECTIONS|ENTRY|KEEP|AT|LOADADDR|ADDR|SIZEOF|ALIGN|ORIGIN|LENGTH|PROVIDE|ASSERT|NOLOAD|SORT|EXCLUDE_FILE|OUTPUT_FORMAT|OUTPUT_ARCH)\\b' },
      { name: 'entity.name.section.ld', match: '\\.[A-Za-z_][A-Za-z_0-9.]*' },
    ],
  },
  {
    name: 'gdb', scopeName: 'source.gdb',
    patterns: [
      { name: 'comment.line.gdb', match: '#.*$' },
      { name: 'string.quoted.double.gdb', begin: '"', end: '"' },
      { name: 'variable.other.gdb', match: '\\$[A-Za-z_][A-Za-z_0-9]*' },
      { name: 'constant.numeric.gdb', match: '\\b(?:0[xX][0-9a-fA-F]+|[0-9]+)\\b' },
      { name: 'keyword.control.gdb', match: '\\b(?:target|remote|monitor|reset|halt|load|break|b|continue|c|step|s|next|n|print|p|x|info|set|watch|layout|disassemble|file|run|quit|bt)\\b' },
    ],
  },
  {
    name: 'armasm', scopeName: 'source.asm.arm',
    aliases: ['s', 'arm-asm'],
    patterns: [
      { name: 'comment.block.armasm', begin: '/\\*', end: '\\*/' },
      { name: 'comment.line.armasm', match: '@.*$' },
      { name: 'keyword.control.directive.armasm', match: '^\\s*\\.[A-Za-z_][A-Za-z_0-9]*' },
      { name: 'entity.name.function.armasm', match: '^[A-Za-z_][A-Za-z_0-9.]*:' },
      { name: 'keyword.control.armasm', match: '\\b(?:ldr|ldrb|ldrh|ldrsb|ldrsh|str|strb|strh|mov|movs|movw|movt|add|adds|adc|adr|sub|subs|sbc|rsb|cmp|cmn|tst|teq|and|ands|orr|orrs|eor|bic|mvn|mul|muls|udiv|sdiv|lsl|lsls|lsr|lsrs|asr|asrs|sxtb|sxth|uxtb|uxth|rev|rev16|clz|bfc|bfi|push|pop|nop|bkpt|wfi|wfe|sev|yield|dsb|dmb|isb|mrs|msr|svc|cpsid|cpsie|b|bl|blx|bx|cbz|cbnz|beq|bne|bhi|bls|bcc|bcs|bgt|ble|bge|blt|bal|it|ite|itt|itte|ittt|ittte|itttt|ittttt)\\b' },
      { name: 'variable.other.register.armasm', match: '\\b(?:r1[0-5]|r[0-9]|sp|lr|pc|psr|xpsr|apsr|primask|basepri|faultmask|control|fpscr)\\b' },
      { name: 'constant.numeric.armasm', match: '#?(?:0[xX][0-9a-fA-F]+|\\d+)' },
      { name: 'variable.other.symbol.armasm', match: '\\b[A-Za-z_][A-Za-z_0-9]*\\b' },
    ],
  },
]
