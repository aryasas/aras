/**
 * LogicEvaluator: A safe and lightweight expression evaluator for "depends_on" metadata.
 * Supports comparison (==, !=, >, <, >=, <=) and logical (&&, ||, !) operators.
 * Avoids 'eval' and 'new Function' for security and stability.
 */

export class LogicEvaluator {
  /**
   * Evaluates a logical expression against a data object.
   * Example: "status == 'Rejected' && total_amount > 1000"
   */
  static evaluate(expression: string, data: Record<string, any>): boolean {
    if (!expression || expression.trim() === "") return true;

    try {
      // 1. Tokenize and normalize
      const tokens = this.tokenize(expression);
      if (tokens.length === 0) return true;

      // 2. Evaluate using a simple recursive descent approach
      return this.evaluateExpression(tokens, data);
    } catch (e) {
      console.error("LogicEvaluator error:", e, "Expression:", expression);
      return true; // Default to visible on error to avoid breaking the UI
    }
  }

  private static tokenize(expr: string): string[] {
    // Split by operators and keep them
    // Supports: &&, ||, ==, !=, >=, <=, >, <, !, (, )
    return expr
      .split(/(&&|\|\||==|!=|>=|<=|>|<|!|\(|\))/g)
      .map(t => t.trim())
      .filter(t => t !== "");
  }

  private static evaluateExpression(tokens: string[], data: Record<string, any>): boolean {
    // Simplified: We'll evaluate level by level (OR, then AND, then Comparisons)
    
    // Handle OR (||)
    if (tokens.includes('||')) {
      const parts = this.splitByOperator(tokens, '||');
      return parts.some(part => this.evaluateExpression(part, data));
    }

    // Handle AND (&&)
    if (tokens.includes('&&')) {
      const parts = this.splitByOperator(tokens, '&&');
      return parts.every(part => this.evaluateExpression(part, data));
    }

    // Handle Comparisons
    if (tokens.length >= 3) {
      const [left, op, right] = tokens;
      const leftVal = this.getValue(left, data);
      const rightVal = this.getValue(right, data);

      switch (op) {
        case '==': return leftVal == rightVal;
        case '!=': return leftVal != rightVal;
        case '>':  return Number(leftVal) >  Number(rightVal);
        case '<':  return Number(leftVal) <  Number(rightVal);
        case '>=': return Number(leftVal) >= Number(rightVal);
        case '<=': return Number(leftVal) <= Number(rightVal);
      }
    }

    // Handle single value (e.g., "!is_active")
    if (tokens[0] === '!') {
      return !this.getValue(tokens[1], data);
    }

    // Default: Check if the value itself is truthy
    return !!this.getValue(tokens[0], data);
  }

  private static splitByOperator(tokens: string[], operator: string): string[][] {
    const result: string[][] = [];
    let current: string[] = [];
    
    for (const token of tokens) {
      if (token === operator) {
        result.push(current);
        current = [];
      } else {
        current.push(token);
      }
    }
    result.push(current);
    return result;
  }

  private static getValue(token: string, data: Record<string, any>): any {
    if (!token) return undefined;

    // Handle Strings
    if ((token.startsWith("'") && token.endsWith("'")) || (token.startsWith('"') && token.endsWith('"'))) {
      return token.slice(1, -1);
    }

    // Handle Booleans
    if (token === 'true') return true;
    if (token === 'false') return false;
    if (token === 'null') return null;

    // Handle Numbers
    if (!isNaN(Number(token))) return Number(token);

    // Handle Field Access
    return data[token];
  }
}
