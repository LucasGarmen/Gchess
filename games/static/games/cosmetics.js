window.GchessPieceUrl=function(pieceKey){
 var style=document.body?document.body.dataset.pieces:'rustic';
 if(!["club", "modern", "tournament", "gold", "silver", "copper", "obsidian", "ivory", "jade", "ruby", "sapphire", "amethyst", "lava", "ice", "rose", "bronze", "pearl", "midnight", "sandstone"].includes(style))return '/static/games/pieces-rustic/'+pieceKey+'.png?v=2';
 return '/static/games/pieces-'+style+'/'+pieceKey+'.svg?v=1';
};
