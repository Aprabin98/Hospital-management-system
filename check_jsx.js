const fs = require('fs');
const file = 'c:\\Users\\aprab\\Desktop\\Hospital management system\\frontend\\src\\components\\Dashboard\\Dashboard.tsx';
const content = fs.readFileSync(file, 'utf8').split('\n');

let depth = 0;

for (let i = 0; i < content.length; i++) {
  const openTags = (content[i].match(/<[a-z][^/>]*(?:\/>|>)/gi) || []);
  const selfClosing = (content[i].match(/<[a-z][^/>]*\/>/gi) || []).length;
  const opens = openTags.length - selfClosing;
  const closeTags = (content[i].match(/<\/[a-z][^>]*>/gi) || []).length;
  
  depth += opens - closeTags;
  
  // Show lines where are JSX tags or around the main return closing
  if ((opens > 0 || closeTags > 0) || (i >= 215 && i <= 230)) {
    console.log(`Line ${i+1}: Opens: ${opens}, Closes: ${closeTags}, Depth: ${depth} | ${content[i].substring(0, 100)}`);
  }
}

console.log(`\nFinal depth at EOF: ${depth}`);
