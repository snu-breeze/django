(function () {
	"use strict";

	var RefundForm = function (el, opts) { this.construct(el, opts); };

	RefundForm.prototype.construct = function (el, opts ) {
		this.state = {
			customAmount: false
		};

		// Cache elements
		this.$el = $(el);
		this.$checkboxes = this.$el.find('input[type="checkbox"]:not(:disabled)');
		this.$refundAmountText = this.$el.find('.js-total-refund-money');
		this.$refundItemCountText = this.$el.find('.js-total-refund-items');
		this.$refundItemCountNoun = this.$el.find('.js-refund-items-noun');
		this.$customAmountWrapper = this.$el.find('.js-total-refund-money-custom');
		this.$customAmountInput = this.$customAmountWrapper.find('input');
		this.$customAmountTrigger = this.$el.find('.js-custom-amount-trigger');
		this.$defaultAmountTrigger = this.$el.find('.js-default-amount-trigger');

		// Some useful values
		this.currency = this.$el.data('currency');
		this.maxAmount = parseFloat(this.$el.data('max-refund'));

		// Set listeners
		this.$el.on('change', 'input[type="checkbox"]:not(:disabled)', _.bind(this.render, this));
		this.$el.on('click', '.js-custom-amount-trigger, .js-default-amount-trigger', _.bind(this.toggleCustomAmount, this));

		// Update state
		if (this.$customAmountInput.val() !== "" && this.calculateDefaultAmount() !== parseFloat(this.$customAmountInput.val())) {
			this.state.customAmount = true;
		}

		this.render();
	};

	RefundForm.prototype.formatMoney = function (amount) {
		return brambling.filters.formatMoney(amount, this.currency);
	};

	RefundForm.prototype.render = function () {
		var checkedRefundItems = this.$checkboxes.filter(":checked");
		var priceTotal = this.calculateDefaultAmount();
		var countTotal = checkedRefundItems.length;

		this.$refundAmountText.html(this.formatMoney(priceTotal));
		this.$refundItemCountText.html(countTotal);
		this.$refundItemCountNoun.html(countTotal !== 1 ? "items" : "item");

		if (this.state.customAmount) {
			this.$refundAmountText.addClass('hidden');
			this.$customAmountTrigger.addClass('hidden');
			this.$customAmountWrapper.removeClass('hidden');
			this.$defaultAmountTrigger.removeClass('hidden');
		} else {
			this.$refundAmountText.removeClass('hidden');
			this.$customAmountTrigger.removeClass('hidden');
			this.$customAmountWrapper.addClass('hidden');
			this.$defaultAmountTrigger.addClass('hidden');
			if (!this.state.customAmount) this.$customAmountInput.val(priceTotal);
		}
	};

	RefundForm.prototype.calculateDefaultAmount = function () {
		var checkedRefundItems = this.$checkboxes.filter(":checked").toArray();
		var totalRefundItems = this.$checkboxes;

		// If there are no items to refund or all items have been refunded
		// already, default to max amount
		if (totalRefundItems.length === 0) return this.maxAmount;

		var amount = _.reduce(checkedRefundItems, function (memo, el) {
			return memo + parseFloat($(el).data('item-price'));
		}, 0);
		return Math.min(amount, this.maxAmount);
	};

	RefundForm.prototype.toggleCustomAmount = function () {
		this.state.customAmount = !this.state.customAmount;
		this.render();
	};

	// Bind to the HTML
	$(function () {
		$('.js-refund-form').each(function () {
			var $this = $(this);
			if (!!$this.data('refundform')) return;
			$this.data('refundform', new RefundForm(this));
		});
	});
}());
