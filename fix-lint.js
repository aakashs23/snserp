const fs = require('fs');
const glob = require('glob');

const files = glob.sync('frontend/**/*.tsx');

files.forEach(file => {
  let content = fs.readFileSync(file, 'utf8');
  let original = content;

  // Replace useEffect(() => { someFunction() }, [someFunction])
  content = content.replace(
    /useEffect\(\(\) => \{\n\s*([a-zA-Z0-9_]+)\(\)\n\s*\}, \[([a-zA-Z0-9_]+)\]\)/g,
    'useEffect(() => {\n    const t = setTimeout(() => $1(), 0)\n    return () => clearTimeout(t)\n  }, [$2])'
  );

  if (file.includes('app-sidebar.tsx')) {
    content = content.replace('Avatar, AvatarFallback, ', '');
    content = content.replace('AvatarFallback, ', '');
    content = content.replace('Bot, ', '');
  }
  
  if (file.includes('users/page.tsx')) {
    content = content.replace(/: any/g, ': unknown');
    content = content.replace("you don't", "you don&apos;t");
  }

  if (file.includes('invoices/register/page.tsx')) {
    content = content.replace('Download, ', '');
  }

  if (file.includes('loans/page.tsx')) {
    content = content.replace('CardDescription, ', '');
    content = content.replace(/"Add Loan"/g, '&quot;Add Loan&quot;');
  }

  if (file.includes('revenue/page.tsx')) {
    content = content.replace('TrendingUp, ', '');
    content = content.replace('Users, ', '');
  }

  if (content !== original) {
    fs.writeFileSync(file, content, 'utf8');
    console.log(`Updated ${file}`);
  }
});
