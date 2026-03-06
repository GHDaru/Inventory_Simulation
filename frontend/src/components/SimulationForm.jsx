import { useState } from 'react';

const DEFAULT_PRODUCT = {
  name: 'Product A',
  initial_stock: 100,
  stock_policy_params: {
    product: 'Product A',
    type: 'minmax',
    min_level: 20,
    max_level: 150,
    lead_time: 5,
    lot_size: null,
  },
  demand_params: {
    distribution_type: 'normal',
    params: { mean: 10, std_dev: 2 },
  },
};

function ProductForm({ product, onChange, onRemove, uploadedData }) {
  const policy = product.stock_policy_params;
  const demand = product.demand_params;

  function set(path, value) {
    const parts = path.split('.');
    // Guard against prototype pollution: reject any segment that targets
    // built-in prototype properties.
    const dangerous = new Set(['__proto__', 'prototype', 'constructor']);
    if (parts.some(p => dangerous.has(p))) return;

    const updated = JSON.parse(JSON.stringify(product));
    let node = updated;
    for (let i = 0; i < parts.length - 1; i++) {
      const key = parts[i];
      if (!Object.prototype.hasOwnProperty.call(node, key)) return;
      node = node[key];
    }
    const lastKey = parts[parts.length - 1];
    if (Object.prototype.hasOwnProperty.call(node, lastKey)) {
      node[lastKey] = value;
    }
    // keep policy.product in sync with product name
    if (path === 'name') updated.stock_policy_params.product = value;
    onChange(updated);
  }

  return (
    <div className="product-form">
      <div className="form-row">
        <label>Product name</label>
        <input value={product.name} onChange={e => set('name', e.target.value)} />
      </div>
      <div className="form-row">
        <label>Initial stock</label>
        <input type="number" min={0} value={product.initial_stock}
          onChange={e => set('initial_stock', parseInt(e.target.value, 10) || 0)} />
      </div>

      <fieldset>
        <legend>Demand</legend>
        {uploadedData ? (
          <p className="info-text">
            Using uploaded historical data ({uploadedData.rows} records, mean&nbsp;
            {uploadedData.mean.toFixed(1)})
          </p>
        ) : (
          <>
            <div className="form-row">
              <label>Distribution</label>
              <select value={demand.distribution_type}
                onChange={e => set('demand_params.distribution_type', e.target.value)}>
                <option value="normal">Normal</option>
                <option value="poisson">Poisson</option>
              </select>
            </div>
            {demand.distribution_type === 'normal' ? (
              <>
                <div className="form-row">
                  <label>Mean</label>
                  <input type="number" step="0.1" value={demand.params.mean}
                    onChange={e => set('demand_params.params.mean', parseFloat(e.target.value) || 0)} />
                </div>
                <div className="form-row">
                  <label>Std dev</label>
                  <input type="number" step="0.1" min={0} value={demand.params.std_dev}
                    onChange={e => set('demand_params.params.std_dev', parseFloat(e.target.value) || 0)} />
                </div>
              </>
            ) : (
              <div className="form-row">
                <label>Lambda (λ)</label>
                <input type="number" step="0.1" min={0} value={demand.params.lambda ?? 10}
                  onChange={e => set('demand_params.params.lambda', parseFloat(e.target.value) || 0)} />
              </div>
            )}
          </>
        )}
      </fieldset>

      <fieldset>
        <legend>Stock policy</legend>
        <div className="form-row">
          <label>Policy type</label>
          <select value={policy.type} onChange={e => set('stock_policy_params.type', e.target.value)}>
            <option value="minmax">Min / Max</option>
            <option value="lot_size">Lot size</option>
          </select>
        </div>
        <div className="form-row">
          <label>Min level (reorder point)</label>
          <input type="number" min={0} value={policy.min_level ?? ''}
            onChange={e => set('stock_policy_params.min_level', parseInt(e.target.value, 10) || 0)} />
        </div>
        {policy.type === 'minmax' ? (
          <div className="form-row">
            <label>Max level</label>
            <input type="number" min={0} value={policy.max_level ?? ''}
              onChange={e => set('stock_policy_params.max_level', parseInt(e.target.value, 10) || 0)} />
          </div>
        ) : (
          <div className="form-row">
            <label>Lot size</label>
            <input type="number" min={1} value={policy.lot_size ?? ''}
              onChange={e => set('stock_policy_params.lot_size', parseInt(e.target.value, 10) || 1)} />
          </div>
        )}
        <div className="form-row">
          <label>Lead time (days)</label>
          <input type="number" min={0} value={policy.lead_time}
            onChange={e => set('stock_policy_params.lead_time', parseInt(e.target.value, 10) || 0)} />
        </div>
      </fieldset>

      <button className="btn-remove" type="button" onClick={onRemove}>Remove product</button>
    </div>
  );
}

export default function SimulationForm({ onSubmit, uploadedData, loading }) {
  const [days, setDays] = useState(90);
  const [products, setProducts] = useState([JSON.parse(JSON.stringify(DEFAULT_PRODUCT))]);

  function addProduct() {
    const newP = JSON.parse(JSON.stringify(DEFAULT_PRODUCT));
    newP.name = `Product ${String.fromCharCode(65 + products.length)}`;
    newP.stock_policy_params.product = newP.name;
    setProducts([...products, newP]);
  }

  function updateProduct(idx, updated) {
    const next = [...products];
    next[idx] = updated;
    setProducts(next);
  }

  function removeProduct(idx) {
    setProducts(products.filter((_, i) => i !== idx));
  }

  function handleSubmit(e) {
    e.preventDefault();
    const payload = {
      days,
      products: products.map(p => {
        const prod = JSON.parse(JSON.stringify(p));
        if (uploadedData) {
          prod.historical_data = uploadedData.historical_data;
          prod.demand_params = null;
        }
        return prod;
      }),
    };
    onSubmit(payload);
  }

  return (
    <form className="simulation-form" onSubmit={handleSubmit}>
      <div className="form-row">
        <label><strong>Simulation days</strong></label>
        <input type="number" min={1} max={3650} value={days}
          onChange={e => setDays(parseInt(e.target.value, 10) || 1)} />
      </div>

      <h3>Products</h3>
      {products.map((p, i) => (
        <details key={i} open={i === 0}>
          <summary>{p.name}</summary>
          <ProductForm
            product={p}
            onChange={updated => updateProduct(i, updated)}
            onRemove={() => removeProduct(i)}
            uploadedData={uploadedData}
          />
        </details>
      ))}

      <div className="form-actions">
        <button type="button" className="btn-secondary" onClick={addProduct}>
          + Add product
        </button>
        <button type="submit" className="btn-primary" disabled={loading || products.length === 0}>
          {loading ? 'Running…' : 'Run simulation'}
        </button>
      </div>
    </form>
  );
}
