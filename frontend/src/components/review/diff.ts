// Word-level diff used by the suggested-change view.
//
// Why not a library? The requirement is a readable, small comparison of two
// short passages. An LCS over word tokens is ~30 lines, has no dependency cost,
// and lets us render additions/deletions as separate segments so the UI can
// style them. Diffing the whole DocumentIR would be the wrong granularity: the
// user is reviewing one proposed rewrite, not a git history.

export type DiffOp = 'equal' | 'added' | 'removed';

export interface DiffSegment {
  op: DiffOp;
  text: string;
}

const MAX_TOKENS = 1200;

function tokenize(text: string): string[] {
  // Keep whitespace attached so the reconstruction reads naturally.
  return text.match(/\s+|[^\s]+/g) ?? [];
}

/** Longest-common-subsequence diff over tokens. */
export function diffWords(before: string, after: string): DiffSegment[] {
  const a = tokenize(before);
  const b = tokenize(after);

  if (a.length > MAX_TOKENS || b.length > MAX_TOKENS) {
    return [
      { op: 'removed', text: before },
      { op: 'added', text: after },
    ];
  }

  const rows = a.length + 1;
  const cols = b.length + 1;
  const table: number[][] = Array.from({ length: rows }, () => new Array(cols).fill(0));

  for (let i = a.length - 1; i >= 0; i -= 1) {
    for (let j = b.length - 1; j >= 0; j -= 1) {
      table[i][j] =
        a[i] === b[j] ? table[i + 1][j + 1] + 1 : Math.max(table[i + 1][j], table[i][j + 1]);
    }
  }

  const segments: DiffSegment[] = [];
  const push = (op: DiffOp, text: string) => {
    const last = segments[segments.length - 1];
    if (last && last.op === op) last.text += text;
    else segments.push({ op, text });
  };

  let i = 0;
  let j = 0;
  while (i < a.length && j < b.length) {
    if (a[i] === b[j]) {
      push('equal', a[i]);
      i += 1;
      j += 1;
    } else if (table[i + 1][j] >= table[i][j + 1]) {
      push('removed', a[i]);
      i += 1;
    } else {
      push('added', b[j]);
      j += 1;
    }
  }
  while (i < a.length) {
    push('removed', a[i]);
    i += 1;
  }
  while (j < b.length) {
    push('added', b[j]);
    j += 1;
  }
  return segments;
}

/** True when the two texts differ only by whitespace/case (a weak change). */
export function isTrivialChange(before: string, after: string): boolean {
  return before.replace(/\s+/g, ' ').trim().toLowerCase() ===
    after.replace(/\s+/g, ' ').trim().toLowerCase();
}
