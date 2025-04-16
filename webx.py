from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Local MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['product']
collection = db['product']

# Helper to convert ObjectId to string
def serialize_product(product):
    if '_id' in product:
        product['_id'] = str(product['_id'])
    return product

@app.route('/checkUID', methods=['GET'])
def check_uid():
    uid = request.args.get('uid')
    if not uid:
        return jsonify({'error': 'UID is required'}), 400

    product = collection.find_one({'UID': uid})
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    return jsonify({'success': True, 'product': serialize_product(product)})

@app.route('/purchaseProduct', methods=['POST'])
def purchase_product():
    uid = request.json.get('uid')
    if not uid:
        return jsonify({'error': 'UID is required'}), 400

    product = collection.find_one({'UID': uid})
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if product['ProductOwner'] == 'supermarket':
        result = collection.update_one({'UID': uid}, {'$set': {'ProductOwner': 'swayam_raut'}})
        if result.modified_count > 0:
            updated_product = collection.find_one({'UID': uid})
            return jsonify({'success': True, 'message': 'Product purchased successfully', 'product': serialize_product(updated_product)})
        else:
            return jsonify({'error': 'Product update failed'}), 400
    else:
        return jsonify({'success': True, 'message': 'Product already owned', 'product': serialize_product(product)})

@app.route('/returnProduct', methods=['POST'])
def return_product():
    uid = request.json.get('uid')
    if not uid:
        return jsonify({'error': 'UID is required'}), 400

    result = collection.update_one(
        {'UID': uid, 'ProductOwner': 'swayam_raut'},
        {'$set': {'ProductOwner': 'supermarket'}}
    )

    if result.modified_count > 0:
        return jsonify({'success': True, 'message': 'Product returned to supermarket'})
    else:
        return jsonify({'error': 'Product not found or not owned by swayam_raut'}), 404

@app.route('/purchases', methods=['GET'])
def get_purchases():
    products = list(collection.find({'ProductOwner': 'swayam_raut'}))
    return jsonify([serialize_product(p) for p in products])

# ✅ New endpoint to add a product
@app.route('/addProduct', methods=['POST'])
def add_product():
    data = request.json
    required_fields = ['ProductName', 'ProductOwner', 'ProductPrice', 'ImageLink', 'UID', 'catNumber']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing fields in request'}), 400

    result = collection.insert_one(data)
    return jsonify({'success': True, 'message': 'Product added successfully', 'id': str(result.inserted_id)})

@app.route('/deleteProduct', methods=['DELETE'])
def delete_product():
    data = request.get_json(force=True)
    uid = data.get('UID')

    if not uid:
        return jsonify({"error": "UID is required"}), 400

    result = collection.delete_one({"UID": uid})
    if result.deleted_count > 0:
        return jsonify({"success": True, "message": "Product deleted successfully"})
    else:
        return jsonify({"error": "Product not found"}), 404
    

@app.route('/inventory-summary', methods=['GET'])
def inventory_summary():
    try:
        pipeline = [
            {'$match': {'ProductOwner': 'supermarket'}},
            {'$group': {'_id': '$catNumber', 'totalItems': {'$sum': 1}}}
        ]
        summary = list(collection.aggregate(pipeline))
        return jsonify(summary), 200
    except Exception as e:
        print('Error processing request:', e)
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/getAllProducts', methods=['GET'])
def get_all_products():
    try:
        collection = db['product']  # Assuming 'product' is your collection name
        all_products = list(collection.find({}, {'_id': False}))
        return jsonify(all_products), 200
    except Exception as e:
        print("Error fetching products:", e)
        return jsonify({"error": "Internal Server Error"}), 500



if __name__ == '__main__':
    app.run(port=3001, debug=True)
