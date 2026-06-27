const fs = require('fs');
const glob = require('glob');

const files = glob.sync('frontend/**/*.tsx');

files.forEach(file => {
  let content = fs.readFileSync(file, 'utf8');
  let original = content;

  // We only want to revert specific cases where unknown broke things
  // 1. .map((entry: unknown) =>
  content = content.replace(/\(entry: unknown\)/g, '(entry: any)');
  
  // 2. error catch block error type? It was `catch (e)` and I removed it entirely or used `catch {`.
  
  // 3. body type
  if (file.includes('users/page.tsx')) {
    content = content.replace('Record<string, unknown>', 'Record<string, any>');
  }

  if (content !== original) {
    fs.writeFileSync(file, content, 'utf8');
    console.log(`Updated ${file}`);
  }
});
