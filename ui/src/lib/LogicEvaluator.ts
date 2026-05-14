/**
 * LogicEvaluator: A lightweight expression evaluator for "depends_on" metadata.
 * Supports comparison (==, !=, >, <, >=, <=) and logical (&&, ||, !) operators.
 */

export class LogicEvaluator {
  /**
   * Evaluates a logical expression against a data object.
   * Example: "status == 'Rejected' && total_amount > 1000"
   */
  static evaluate(expression: string, data: Record<string, any>): boolean {
    if (!expression || expression.trim() === "") return true;

    try {
      // 1. Tokenize the expression
      const tokens = this.tokenize(expression);
      
      // 2. Parse and evaluate (simplified recursive descent or shunting-yard)
      // For MVP, we'll use a safer Function constructor approach with strict sandboxing
      // or a simple manual parser. Given the complexity of && and ||, a basic parser is better.
      return this.parseAndEval(tokens, data);
    } catch (e) {
      console.error("LogicEvaluator error:", e, "Expression:", expression);
      return true; // Default to visible on error to avoid breaking the UI
    }
  }

  private static tokenize(expr: string): string[] {
    // Regex to split by operators while preserving them, and handling strings
    // Operators: &&, ||, ==, !=, >=, <=, >, <, !, (, )
    return expr
      .split(/(&&|\|\||==|!=|>=|<=|>|<|!|\(|\))/g)
      .map(t => t.trim())
      .filter(t => t !== "");
  }

  private static parseAndEval(tokens: string[], data: Record<string, any>): boolean {
    // Basic implementation: replace field names with values and use a simple evaluator
    // This is a placeholder for a more robust parser.
    // For now, let's support the most common case: "field OP value" and combinations with &&
    
    const processedTokens = tokens.map(token => {
      if (['&&', '||', '==', '!=', '>=', '<=', '>', '<', '!', '(', ')'].includes(token)) {
        return token;
      }
      
      // Handle strings 'val' or "val"
      if ((token.startsWith("'") && token.endsWith("'")) || (token.startsWith('"') && token.endsWith('"'))) {
        return JSON.stringify(token.slice(1, -1));
      }

      // Handle numbers
      if (!isNaN(Number(token))) {
        return token;
      }

      // Handle booleans
      if (token === 'true' || token === 'false') {
        return token;
      }

      // Handle null/undefined
      if (token === 'null') return 'null';

      // It's a field name
      const val = data[token];
      return JSON.stringify(val);
    });

    try {
      // Safer alternative to eval() for basic logical expressions
      // We only allow logical and comparison operators
      const safeExpr = processedTokens.join(' ');
      
      // Simple validation: only allowed characters
      if (/[^a-zA-Z0-9\s"'.&|!=><!()[\]{}_-]/g.test(safeExpr)) {
        throw new Error("Forbidden characters in expression");
      }

      // Use Function constructor as a scoped sandbox
      // eslint-disable-next-line no-new-func
      return new Function(`return (${safeExpr})`)();
    } catch (e) {
      console.warn("Failed to evaluate expression:", tokens.join(' '), e);
      return true;
    }
  }
}
