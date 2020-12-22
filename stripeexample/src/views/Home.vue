<template>
  <div>
    <div class="grid-center">
      <!-- Use a carousel to show the items gotten from the DB in a GET request -->
      <v-carousel hide-delimiters>
        <!-- Loop through the items and show some cards-->
        <!-- Each item will be accessed at the particular column number (this needs to change to match your DB) -->
        <v-carousel-item v-for="item in items" :key="item[0]">
          <v-row class="fill-height" align="center" justify="center">
            <v-card class="item-card" max-width="300">
              <v-img :src="item[4]" height="200px"></v-img>
              <v-card-title> {{ item[2] }} </v-card-title>
              <v-card-subtitle> {{ item[1] }} </v-card-subtitle>
              <v-card-actions>
                <!-- Button to add the animal to the cart -->
                <!-- When the button is clicked, we call the addToCart function and pass the item id
                and the text to put in the small popup -->
                <v-btn @click="addToCart(item[0], item[1] + ' added to cart!')">
                  Add to Cart
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-row>
        </v-carousel-item>
      </v-carousel>
      <!-- Button to send the purchase to our backend and create the Stripe Session -->
      <v-btn v-if="cart.length > 0" @click="stripeSession()">
        Purchase Animals
      </v-btn>
    </div>
    <!-- This is the small popup that shows what you added to the cart -->
    <div class="text-center">
      <v-snackbar v-model="snackbar" timeout="2000">
        {{ addedText }}
        <template v-slot:action="{ attrs }">
          <v-btn color="blue" text v-bind="attrs" @click="snackbar = false">
            Close
          </v-btn>
        </template>
      </v-snackbar>
    </div>
  </div>
</template>

<script>
import axios from "axios";
// Using the stripe imported from the index.html we setup stripe with our PUBLIC API KEY
const stripe = window.Stripe(
  "pk_test_51HyhiMLF1dk5YLGAIoqk2Z3fj8NigUuuQIuYMGrOqGd6hRatxL916eoKKczp4UoXRpe2CZUGuxojoSRaHF47bHTP0071fUnHfC"
);

export default {
  data() {
    return {
      // All items gotten from the DB
      items: [],
      // Text to show a popup message when you add an animal to the cart
      addedText: "",
      snackbar: false,
      // The cart, an array of id's from the DB
      cart: [],
    };
  },
  mounted() {
    // On mounted we get the items from the DB we are selling
    this.getItems();
  },
  methods: {
    // Simple method to add an ID to the cart, change the message for the popup
    // Set the snackbar variable to true to show the popup for 2 seconds
    addToCart(itemId, message) {
      this.cart.push(itemId);
      this.snackbar = true;
      this.addedText = message;
    },
    // Axios call to GET the items from the DB
    getItems() {
      axios
        .request({
          url: "http://localhost:5000/api/items",
          method: "GET",
        })
        .then((response) => {
          console.log(response.data);
          this.items = response.data;
        })
        .catch((err) => {
          console.log(err);
        });
    },
    // POST request to send our cart to the backend
    stripeSession() {
      axios
        .request({
          url: "http://localhost:5000/api/stripeSession",
          method: "POST",
          data: {
            item_ids: this.cart,
          },
        })
        .then((response) => {
          // VERY IMPORTANT
          // On success we want to redirect our customer to the stripe page
          // We do this by using the stripe library imported and pass the sessionId
          // The response.data.id is sent back from our backend
          stripe.redirectToCheckout({ sessionId: response.data.id });
        })
        .catch((error) => {
          console.log(error);
        });
    },
  },
};
</script>

<style scoped>
</style>