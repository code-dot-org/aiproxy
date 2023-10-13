// GAME SETUP
// create player, target, and obstacles
var player = createSprite(200, 100);
player.setAnimation("player");
player.scale = 0.8;
var burger = createSprite(randomNumber(0,400),randomNumber(0,400));
burger.setAnimation("burger");
burger.scale = 0.2;
burger.setCollider("circle");
var sword = createSprite(-50, randomNumber(0, 400));
sword.setAnimation("sword");
sword.scale = 0.5;
var sword2 = createSprite(randomNumber(0, 400), -50);
sword2.setAnimation("sword2");
sword2.scale = 0.5;
sword.velocityX = 3;
sword2.velocityY = 3;


function draw() {
  background("green");
  
  // FALLING
  player.velocityY+=0.7;
  
  // LOOPING
    if (sword.x>425){
      sword.y=-50;
      sword.x=randomNumber(0, 400);
    }
     if (sword2.x>425){
      sword2.y=-50;
      sword2.x=randomNumber(0, 400);
     }
  
  // PLAYER CONTROLS
  // change the y velocity when the user clicks "up"
    if (keyDown("up")) {
       player.velocityY-=1.5;
     }
      
  // decrease the x velocity when user clicks "left"
      if (keyDown("LEFT")) {
       player.velocityX-=0.1;
       
     }
  // increase the x velocity when the user clicks "right"
     if (keyDown("RIGHT")) {
       player.velocityX+=0.1;
       
     }
  // SPRITE INTERACTIONS
  // reset the coin when the player touches it
      if (player.isTouching(burger)) {
        burger.x=randomNumber(0, 400);
        burger.y=randomNumber(0,400);
      }
      
  // make the obstacles push the player
  sword.displace(player);
  sword2.displace(player);
  // DRAW SPRITES
  drawSprites();
  
  // GAME OVER
  if (player.x < -50 || player.x > 450 || player.y < -50 || player.y > 450) {
    background("black");
    textSize(50);
    fill("blue");
    text("Game Over!", 50, 200);
  }
  
}
