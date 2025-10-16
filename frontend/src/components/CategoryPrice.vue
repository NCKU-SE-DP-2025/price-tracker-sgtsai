<template>
  <div class="category-price-wrapper">
    <h2>{{ categoryName }}</h2>
    <div v-if="isLoading">Loading...</div>
    <div v-if="errorMessage" class="error">{{ errorMessage }}</div>
    <table v-if="!isLoading && !errorMessage">
      <thead>
        <tr>
          <th>商品名稱</th>
          <th>規格</th>
          <th>{{ latestDataTime }} 最新價格</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="data in priceData" :key="data.編號">
          <td>{{ data.產品名稱 }}</td>
          <td>{{ data.規格 }}</td>
          <td>{{ latestPrice(data.統計值) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import { computed } from 'vue';
import Categories from '@/constants/categories';

export default {
  props: {
    category: {
      type: String,
      required: true
    },
    priceData: {
      type: Array,
      required: true
    },
    isLoading: {
      type: Boolean,
      required: true
    },
    errorMessage: {
      type: String,
      required: false
    }
  },
  setup(props) {
    const categoryName = computed(() => Categories[props.category]);

    const latestDataTime = computed(() => {
      if (!props.priceData.length || !props.priceData[0].時間終點) return '';
      const [year, month] = props.priceData[0].時間終點.split('-');
      return `${year}.${month}`;
    });

    const latestPrice = pricesStr => {
      const numbers = pricesStr.split(',').map(Number);
      let i = numbers.length - 1;
      while (i >= 0 && numbers[i] === 0) i--;
      return i === -1 ? '-' : numbers[i];
    };

    return {
      categoryName,
      latestDataTime,
      latestPrice
    };
  }
};
</script>

<style scoped>
.error {
  color: red;
}
table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
}
th, td {
  border: 1px solid #ddd;
  text-align: center;
  padding: 0.5em 1em;
}
th {
  background-color: #355f81;
  color: white;
}
h2 {
  margin-bottom: 0.5em;
  font-size: 1.5em;
  font-weight: bold;
}
.category-price-wrapper {
  background-color: white;
  border-radius: 1em;
  padding: 2em;
}
</style>
