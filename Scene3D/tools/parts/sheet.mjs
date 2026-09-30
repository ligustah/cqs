// tile images into a labelled jpeg grid: node sheet.mjs out.jpg cell a.png b.png ...
import sharp from 'sharp';
const [out, cell, ...ins] = process.argv.slice(2); const C=+cell; const cols=Math.min(4,ins.length), rows=Math.ceil(ins.length/cols);
const layers=[]; for (const [k,f] of ins.entries()) layers.push({input: await sharp(f).resize(C,C,{fit:'contain',background:'#ddd'}).toBuffer(), left:(k%cols)*C, top:Math.floor(k/cols)*C});
await sharp({create:{width:cols*C,height:rows*C,channels:3,background:'#fff'}}).composite(layers).jpeg({quality:82}).toFile(out);
