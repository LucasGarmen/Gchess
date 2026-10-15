const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
for(const file of ['board.js','board.min.js']){
 const src=fs.readFileSync('games/static/games/'+file,'utf8');const start=src.indexOf('function getPremoveCastlingMoves('),end=src.indexOf('function highlightMoves(',start);assert(start>=0&&end>start);
 const rights={white:{},black:{}};const squares={};const context={castlingRights:rights,getSquare:c=>squares[c],coordToPosition:c=>({col:c.charCodeAt(0)-97,row:Number(c[1])-1}),positionToCoord:(c,r)=>c>=0&&c<8&&r>=0&&r<8?String.fromCharCode(97+c)+(r+1):null};vm.createContext(context);vm.runInContext(src.slice(start,end),context);
 for(const [color,rank] of [['white','1'],['black','8']]){
  const king={dataset:{type:'king',color,coord:'e'+rank}};squares['h'+rank]={dataset:{type:'rook',color}};squares['a'+rank]={dataset:{type:'rook',color}};
  let moves=context.getPremoveMoves(king);assert(moves.includes('g'+rank));assert(moves.includes('c'+rank));rights[color].kingMoved=true;assert(!context.getPremoveMoves(king).includes('g'+rank));rights[color].kingMoved=false;rights[color].rightRookMoved=true;assert(!context.getPremoveMoves(king).includes('g'+rank));assert(context.getPremoveMoves(king).includes('c'+rank));rights[color].rightRookMoved=false;delete squares['a'+rank];assert(!context.getPremoveMoves(king).includes('c'+rank));king.dataset.coord='d'+rank;assert(!context.getPremoveCastlingMoves(king).length);
 }
}
console.log('Castling premove: both colors, both sides, moved king/rook and missing rook in source and shipped artifact passed.');
