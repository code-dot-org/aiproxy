// Create alien sprites and assign animations
var alienBlue = createSprite(100, 200);
alienBlue.setAnimation("alienBlue");
var alienGreen = createSprite(250, 575);
alienGreen.setAnimation("alienGreen");
var textY = 500;
var textX = 25;


function draw() { 
  // movement
  textY = textY - 3;
  textX = 25 + randomNumber(-3, 3);
  alienGreen.y = alienGreen.y - 3;
  alienBlue.rotation = random( -5, 5);
  
  // Draw space background and planets
  background("darkblue");
  
  noStroke();
  fill("yellow");
  ellipse(375, -50, 300, 300);
  
  fill("darkgreen");
  ellipse(125, 75, 100, 100);
  
  fill("blue");
  ellipse(350, 350, 150, 150);
  
  // Add joke text
  fill("white");
  textSize(20);
  text("What kind of music do planets sing?", textX, 125);
  text("Neptunes!", 200, textY);
  
  
  drawSprites();
}