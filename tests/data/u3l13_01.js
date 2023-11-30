var backgroundSprite = createSprite(200, 200);
var snowman = createSprite(200, 200);
snowman.setAnimation("snowman");
snowman.scale = 0.25;
var santa = createSprite(300, 350);
santa.scale = 0.25;
function draw() {
  backgroundSprite.setAnimation("backgroundSprite");
  santa.setAnimation("santa");
  santa.x = santa.x + randomNumber(-1, 1);
  snowman.rotation++;
  drawSprites();
}